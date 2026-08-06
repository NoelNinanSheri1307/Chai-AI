"""Refresh-token persistence entity.

Only SHA-256 hashes of raw refresh tokens are stored, never the tokens
themselves. ``revoked_at`` distinguishes active from revoked tokens and
``replaced_by_hash`` supports rotation-chain reuse detection.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Index
from sqlmodel import Field, Relationship

from app.core import constants
from app.models.base import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(CreatedAtMixin, table=True):
    """A refresh-token rotation record belonging to a user."""

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        # Listing a user's active/revoked tokens.
        Index("ix_refresh_tokens_user_id_revoked_at", "user_id", "revoked_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="users.id",
        ondelete="CASCADE",
        index=True,
        nullable=False,
    )
    token_hash: str = Field(
        index=True,
        unique=True,
        nullable=False,
        max_length=constants.PASSWORD_HASH_MAX_LENGTH,
    )
    expires_at: datetime = Field(nullable=False)
    revoked_at: datetime | None = Field(default=None, nullable=True)
    replaced_by_hash: str | None = Field(
        default=None,
        nullable=True,
        max_length=constants.PASSWORD_HASH_MAX_LENGTH,
    )

    user: "User" = Relationship(back_populates="refresh_tokens")
