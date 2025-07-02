# Router utility functions for Thronestead
from fastapi import APIRouter
from typing import Sequence, Iterable


def mirror_router(router: APIRouter, prefix: str, tags: Sequence[str] | None = None) -> APIRouter:
    """Return a new router that exposes the routes from ``router`` under ``prefix``."""
    alt_router = APIRouter(prefix=prefix, tags=list(tags or router.tags))
    alt_router.include_router(router)
    return alt_router

__all__ = ["mirror_router"]
