"""V1 API router aggregating all versioned routers.

Feature routers are mounted here as their milestones are delivered. Today only
the operational ``meta`` router is wired; the routers for auth, analyses,
history, compare and reports exist as named extension points and will be
included as they are implemented.
"""

from fastapi import APIRouter

from app.api.v1 import meta

api_router = APIRouter()
api_router.include_router(meta.router)
