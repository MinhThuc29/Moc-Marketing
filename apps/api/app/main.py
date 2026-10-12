import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_v1_router
from app.api.v1.health import router as health_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("moc-healthy-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Mộc Healthy API service in %s mode...", settings.ENVIRONMENT)
    try:
        from app.core.database import Base, engine, AsyncSessionLocal
        from app.core.seed import (
            seed_roles_and_permissions,
            seed_demo_categories_and_products,
            seed_demo_inventory,
            seed_demo_promotions,
        )
        from app.core.security import get_password_hash
        from app.models.auth import User, Role, user_roles
        from sqlalchemy import select

        if engine and AsyncSessionLocal:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with AsyncSessionLocal() as session:
                await seed_roles_and_permissions(session)

                # Ensure admin user exists
                res = await session.execute(select(User).where(User.email == "admin@mochhealthy.vn"))
                admin_user = res.scalar_one_or_none()
                if not admin_user:
                    res_admin_role = await session.execute(select(Role).where(Role.name == "ADMIN"))
                    admin_role = res_admin_role.scalar_one()
                    admin_user = User(
                        email="admin@mochhealthy.vn",
                        full_name="Quản trị viên Hệ thống",
                        password_hash=get_password_hash("Password@123"),
                        is_active=True,
                        is_superuser=True,
                    )
                    session.add(admin_user)
                    await session.flush()
                    await session.execute(
                        user_roles.insert().values(user_id=admin_user.id, role_id=admin_role.id)
                    )

                    # Also add a marketing user for testing
                    res_mkt_role = await session.execute(select(Role).where(Role.name == "MARKETING"))
                    mkt_role = res_mkt_role.scalar_one()
                    mkt_user = User(
                        email="marketing@mochhealthy.vn",
                        full_name="Nhân viên Marketing",
                        password_hash=get_password_hash("Password@123"),
                        is_active=True,
                        is_superuser=False,
                    )
                    session.add(mkt_user)
                    await session.flush()
                    await session.execute(
                        user_roles.insert().values(user_id=mkt_user.id, role_id=mkt_role.id)
                    )
                    await session.commit()

                # Seed 10 demo products and 5 categories
                await seed_demo_categories_and_products(session, admin_user_id=admin_user.id)
                # Seed demo inventory batches and movements
                await seed_demo_inventory(session, admin_user_id=admin_user.id)
                # Seed demo promotions
                await seed_demo_promotions(session, admin_user_id=admin_user.id)
                # Seed demo marketing campaigns
                from app.core.seed import (
                    seed_demo_campaigns,
                    seed_demo_content_items,
                    seed_demo_analytics_and_attribution,
                    seed_demo_automations,
                    seed_demo_recommendations_and_alerts,
                    seed_demo_social_publishing,
                    seed_demo_ai_templates,
                )
                await seed_demo_campaigns(session, admin_user_id=admin_user.id)
                # Seed demo marketing content items
                await seed_demo_content_items(session, admin_user_id=admin_user.id)
                # Seed demo tracking events and conversion attribution
                await seed_demo_analytics_and_attribution(session, admin_user_id=admin_user.id)
                # Seed demo marketing automation workflows and run logs
                await seed_demo_automations(session, admin_user_id=admin_user.id)
                # Seed demo AI recommendations and smart alerts
                await seed_demo_recommendations_and_alerts(session)
                # Seed demo social connections and publishing records
                await seed_demo_social_publishing(session)
                # Seed demo AI prompt templates and logs
                await seed_demo_ai_templates(session)
            logger.info("Database auto-initialization and demo seed completed.")
    except Exception as e:
        logger.warning("Could not auto-seed database on startup: %s", e)
    yield
    logger.info("Shutting down Mộc Healthy API service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Core backend for Mộc Healthy AI Marketing & Commerce Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_timing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{process_time:.2f}"
    return response


# Include routers
app.include_router(health_router)
app.include_router(api_v1_router, prefix="/api/v1")

# Mount uploads static files
from fastapi.staticfiles import StaticFiles
from app.core.storage import BASE_UPLOAD_DIR
app.mount("/uploads", StaticFiles(directory=str(BASE_UPLOAD_DIR)), name="uploads")


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
    }
