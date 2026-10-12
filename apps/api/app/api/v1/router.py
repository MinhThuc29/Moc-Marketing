from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.products import router as products_router
from app.api.v1.media import router as media_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.promotions import router as promotions_router
from app.api.v1.storefront import router as storefront_router
from app.api.v1.cart import router as cart_router
from app.api.v1.checkout import router as checkout_router
from app.api.v1.orders import router as orders_router
from app.api.v1.omnichannel import router as omnichannel_router
from app.api.v1.customers import router as customers_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.content import router as content_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.tracking import router as tracking_router
from app.api.v1.automation import router as automation_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.social import router as social_router
from app.api.v1.ai import router as ai_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(media_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(promotions_router)
api_v1_router.include_router(storefront_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(checkout_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(omnichannel_router, prefix="/omnichannel", tags=["Omnichannel Commerce Hub"])
api_v1_router.include_router(customers_router)
api_v1_router.include_router(campaigns_router)
api_v1_router.include_router(content_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(tracking_router)
api_v1_router.include_router(automation_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(social_router)
api_v1_router.include_router(ai_router)
