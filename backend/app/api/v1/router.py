"""Only session-authorized routes; legacy admin/upload routers are never mounted."""
from importlib import import_module

from fastapi import APIRouter, Depends

from app.config import settings
from app.api.v1.endpoints import auth
from app.services.auth_service import require_csrf, require_member

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])


def _domain(name: str):
    module_name = f"app.api.v1.endpoints.{name}"
    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        # Isolated foundation tests have no domain implementations. Production never
        # silently drops a module or ignores a missing transitive dependency.
        if settings.ENVIRONMENT == "test" and exc.name == module_name:
            return None
        raise


for name in ("trade", "membership", "documents"):
    module = _domain(name)
    if module is not None:
        api_router.include_router(module.router, tags=[name])
        if hasattr(module, "public_router"):
            api_router.include_router(module.public_router, tags=[name])

# Read routes require membership; mutation dependencies also enforce CSRF+Origin.
for name, prefix in (("analytics", "/analytics"), ("chat", "")):
    module = _domain(name)
    if module is not None:
        api_router.include_router(module.router, prefix=prefix, tags=[name],
                                  dependencies=[Depends(require_member), Depends(require_csrf)])
