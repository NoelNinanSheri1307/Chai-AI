"""Auth router: registration, login, refresh and logout.

Endpoints ``POST /v1/auth/register|login|refresh|logout`` arrive with the
authentication milestone (Milestone 5). Reserved as an extension point; wire
``include_router(auth.router, prefix="/auth")`` into ``router.py`` when
implemented.
"""
