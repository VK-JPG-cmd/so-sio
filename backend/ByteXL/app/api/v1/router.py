from fastapi import APIRouter
from app.api.v1.endpoints import (
    admin,
    analysis,
    auth,
    brand_applications,
    brands,
    health,
    owner_threats,
    reviews,
    threat_reports,
    users,
)

api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(brand_applications.router)
api_v1_router.include_router(brands.router)
api_v1_router.include_router(reviews.router)
api_v1_router.include_router(threat_reports.router)
api_v1_router.include_router(analysis.router)
api_v1_router.include_router(owner_threats.router)
api_v1_router.include_router(admin.router)

