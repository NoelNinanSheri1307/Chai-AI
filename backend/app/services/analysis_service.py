"""Analysis service: upload orchestration and result assembly.

``AnalysisService`` owns the synchronous analysis workflow: it validates the
upload, stores the original blob, persists the ``Analysis`` record, runs the
injected pipeline, persists its result and returns the response DTO.

The service contains orchestration only — no HTTP, no FastAPI objects, no SQL
and no forensic logic. The pipeline is injected; it is never instantiated here.
"""

from __future__ import annotations

import logging

from app.clients.storage import StorageClient
from app.core.config import Settings
from app.core.constants import ANALYSIS_PUBLIC_ID_PREFIX
from app.core.enums import AnalysisStatus
from app.core.errors import ErrorCode
from app.core.exceptions import AnalysisNotFoundError, ChaiError
from app.core.logging import get_request_id
from app.models.analysis import Analysis
from app.pipeline.base import AnalysisPipeline, PipelineResult
from app.repos.analysis_repo import AnalysisRepository
from app.schemas.analysis import AnalysisResultDTO
from app.services.mappers import analysis_to_result_dto
from app.utils import keys
from app.utils.image import validate_image_upload

logger = logging.getLogger(__name__)


class AnalysisService:
    """Coordinate upload, pipeline execution and persistence for one analysis."""

    def __init__(
        self,
        *,
        analysis_repo: AnalysisRepository,
        storage: StorageClient,
        pipeline: AnalysisPipeline,
        settings: Settings,
    ) -> None:
        self._analysis_repo = analysis_repo
        self._storage = storage
        self._pipeline = pipeline
        self._settings = settings

    def analyze_upload(
        self,
        *,
        data: bytes,
        content_type: str | None,
        file_name: str | None,
        user_id: int | None = None,
    ) -> AnalysisResultDTO:
        """Validate, store, analyze and persist an uploaded image.

        Returns the completed ``AnalysisResultDTO``. Raises the catalog upload
        errors (413/415/422) when validation fails and ``pipeline_error`` if the
        pipeline cannot produce a result.
        """
        mime = validate_image_upload(
            data, content_type=content_type, filename=file_name
        )

        public_id = keys.new_public_id(ANALYSIS_PUBLIC_ID_PREFIX)
        original_key = keys.original_storage_key(self._settings.environment, data, mime)
        self._storage.store(original_key, data, content_type=mime)

        analysis = self._analysis_repo.create(
            Analysis(
                public_id=public_id,
                user_id=user_id,
                original_key=original_key,
                file_name=file_name,
                mime_type=mime,
                status=AnalysisStatus.RUNNING,
            )
        )

        logger.info(
            "Analysis created",
            extra={
                "request_id": get_request_id(),
                "analysis_public_id": public_id,
                "original_key": original_key,
                "size_bytes": len(data),
            },
        )

        result = self._run_pipeline(analysis, data, mime, file_name)
        self._analysis_repo.persist_result(analysis, result)

        logger.info(
            "Analysis completed",
            extra={
                "request_id": get_request_id(),
                "analysis_public_id": public_id,
                "verdict": result.verdict.value,
            },
        )
        return analysis_to_result_dto(analysis)

    def get_analysis(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> AnalysisResultDTO:
        """Return the stored analysis for ``public_id`` as its result DTO."""
        analysis = self.get_analysis_entity(public_id, user_id=user_id)
        return analysis_to_result_dto(analysis)

    def get_analysis_entity(
        self,
        public_id: str,
        *,
        user_id: int | None = None,
    ) -> Analysis:
        """Return the stored ORM analysis for ``public_id``.

        Exposed for service-to-service composition (for example the comparison
        flow needs the persisted entity to link it). Raises
        :class:`AnalysisNotFoundError` (HTTP 404) when missing.
        """
        analysis = self._analysis_repo.get_for_user(user_id, public_id)
        if analysis is None:
            raise AnalysisNotFoundError(public_id)
        return analysis

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _run_pipeline(
        self,
        analysis: Analysis,
        data: bytes,
        mime: str,
        file_name: str | None,
    ) -> PipelineResult:
        """Run the injected pipeline and return its result.

        On failure the analysis is stamped ``failed`` and the error is re-raised
        as a catalog ``pipeline_error`` so the transaction rolls back.
        """
        try:
            return self._pipeline.analyze(data, content_type=mime, file_name=file_name)
        except Exception:
            analysis.status = AnalysisStatus.FAILED
            self._analysis_repo.flush()
            logger.exception(
                "Pipeline failed",
                extra={
                    "request_id": get_request_id(),
                    "analysis_public_id": analysis.public_id,
                },
            )
            raise ChaiError(
                ErrorCode.PIPELINE_ERROR,
                "The analysis pipeline failed to produce a result.",
            ) from None
