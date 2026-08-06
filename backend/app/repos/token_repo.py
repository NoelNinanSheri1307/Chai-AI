"""Token repository: refresh-token lifecycle.

Only token hashes are ever stored or queried; raw tokens never reach this
layer.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import update
from sqlmodel import Session

from app.models.refresh_token import RefreshToken
from app.repos.base import BaseRepository


class TokenRepository(BaseRepository[RefreshToken]):
    """Persistence for :class:`RefreshToken` records."""

    model = RefreshToken

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_token_hash(
        self,
        token_hash: str,
        *,
        include_revoked: bool = True,
    ) -> RefreshToken | None:
        """Return the token with the given hash, optionally including revoked."""
        statement = self._base_select()
        if not include_revoked:
            statement = statement.where(RefreshToken.revoked_at.is_(None))
        statement = statement.where(RefreshToken.token_hash == token_hash)
        return self.session.scalars(statement).first()

    def list_active_for_user(self, user_id: int) -> list[RefreshToken]:
        """Return every active (unrevoked) token belonging to a user."""
        statement = (
            self._base_select()
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .order_by(RefreshToken.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def revoke(
        self,
        token: RefreshToken,
        *,
        replaced_by_hash: str | None = None,
    ) -> RefreshToken:
        """Revoke a token, optionally linking the hash that replaced it."""
        token.revoked_at = datetime.now(timezone.utc)
        if replaced_by_hash is not None:
            token.replaced_by_hash = replaced_by_hash
        self.session.flush()
        return token

    def revoke_all_for_user(self, user_id: int) -> int:
        """Revoke every active token belonging to a user; returns the count."""
        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        result = self.session.exec(statement)
        self.session.flush()
        return result.rowcount or 0
