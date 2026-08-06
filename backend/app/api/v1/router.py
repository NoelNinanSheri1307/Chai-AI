"""V1 API router aggregating all versioned routers.

The operational ``meta`` router plus the application-core feature routers
(analyses, history, compare, reports) are mounted here. The ``auth`` router is
a reserved extension point and is wired when authentication is delivered.
"""

from fastapi import APIRouter

from app.api.v1 import analyses, compare, history, meta, reports

api_router = APIRouter()
api_router.include_router(meta.router)
api_router.include_router(analyses.router)
api_router.include_router(history.router)
api_router.include_router(compare.router)
api_router.include_router(reports.router)
