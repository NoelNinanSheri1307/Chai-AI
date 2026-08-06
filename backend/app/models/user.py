"""User persistence entity.

Stores authenticated account records. Passwords are persisted only as hashes;
token and credential policies are the responsibility of the (future)
authentication layer, not this model.
"""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship

from app.core import constants
from app.models.base import SoftDeleteMixin, TimestampMixin, soft_delete_index

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.comparison import Comparison
    from app.models.refresh_token import RefreshToken


class User(TimestampMixin, SoftDeleteMixin, table=True):
    """An authenticated Chai AI account."""

    __tablename__ = "users"
    __table_args__ = (
        soft_delete_index("users"),
        CheckConstraint(
            f"length(email) <= {constants.USER_EMAIL_MAX_LENGTH}",
            name="ck_users_email_length",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(
        index=True,
        unique=True,
        nullable=False,
        max_length=constants.USER_EMAIL_MAX_LENGTH,
    )
    password_hash: str = Field(
        nullable=False, max_length=constants.PASSWORD_HASH_MAX_LENGTH
    )
    display_name: str = Field(
        nullable=False, max_length=constants.DISPLAY_NAME_MAX_LENGTH
    )
    is_active: bool = Field(default=True, nullable=False)

    # Relationships (populated by the ORM; owned by children)
    analyses: list["Analysis"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    comparisons: list["Comparison"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize an email to trimmed lowercase for canonical uniqueness."""
        return email.strip().lower()
