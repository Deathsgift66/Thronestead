from fastapi import APIRouter
from fastapi.routing import APIRoute


def mirror_routes(router: APIRouter, alt_router: APIRouter) -> None:
    """Duplicate routes from ``router`` onto ``alt_router`` with its prefix."""
    base = router.prefix or ""
    alt = alt_router.prefix or ""
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        suffix = route.path[len(base):] if route.path.startswith(base) else route.path
        alt_path = alt + suffix
        alt_router.add_api_route(
            alt_path,
            route.endpoint,
            methods=route.methods,
            name=route.name,
            response_model=route.response_model,
            status_code=route.status_code,
            summary=route.summary,
            description=route.description,
            response_description=route.response_description,
            tags=route.tags,
            dependencies=route.dependencies,
            responses=route.responses,
            deprecated=route.deprecated,
        )

