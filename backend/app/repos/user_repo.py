"""User repository: account persistence and lookup."""

from __future__ import annotations

from sqlmodel import Session

from app.models.user import User
from app.repos.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Persistence for :class:`User` accounts.

    Email lookups normalize their input to trimmed lowercase so queries match
    the canonical form enforced by the model.
    """

    model = User

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        display_name: str,
        is_active: bool = True,
    ) -> User:
        """Create and return a new user account with the given hash.

        The email is normalized to trimmed lowercase to preserve the unique
        canonical form.
        """
        return self.create(
            User(
                email=User.normalize_email(email),
                password_hash=password_hash,
                display_name=display_name,
                is_active=is_active,
            )
        )

    def get_by_email(self, email: str, *, include_deleted: bool = False) -> User | None:
        """Return the user with the given (normalized) email, or ``None``."""
        statement = self._base_select(include_deleted=include_deleted).where(
            User.email == User.normalize_email(email)
        )
        return self.session.scalars(statement).first()

    def email_exists(self, email: str, *, include_deleted: bool = False) -> bool:
        """Return whether a user with the given email already exists."""
        return self.get_by_email(email, include_deleted=include_deleted) is not None
