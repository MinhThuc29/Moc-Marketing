import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.seed import (
    seed_roles_and_permissions,
    seed_demo_categories_and_products,
    seed_demo_inventory,
    seed_demo_promotions,
    seed_demo_campaigns,
    seed_demo_content_items,
    seed_demo_analytics_and_attribution,
    seed_demo_automations,
    seed_demo_recommendations_and_alerts,
    seed_demo_social_publishing,
    seed_demo_ai_templates,
)
from app.core.security import get_password_hash
from app.models.auth import User, Role, user_roles

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    async def init():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with TestSessionLocal() as session:
            await seed_roles_and_permissions(session)

            # Query seeded roles
            res_admin = await session.execute(select(Role).where(Role.name == "ADMIN"))
            admin_role = res_admin.scalar_one()

            res_mkt = await session.execute(select(Role).where(Role.name == "MARKETING"))
            mkt_role = res_mkt.scalar_one()

            res_inv = await session.execute(select(Role).where(Role.name == "INVENTORY"))
            inv_role = res_inv.scalar_one()

            # 1. Admin User
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

            # 2. Marketing User
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

            # 3. Inventory User
            inv_user = User(
                email="inventory@mochhealthy.vn",
                full_name="Thủ kho Mộc Healthy",
                password_hash=get_password_hash("Password@123"),
                is_active=True,
                is_superuser=False,
            )
            session.add(inv_user)
            await session.flush()
            await session.execute(
                user_roles.insert().values(user_id=inv_user.id, role_id=inv_role.id)
            )

            # 4. Inactive User
            inactive_user = User(
                email="inactive@mochhealthy.vn",
                full_name="Tài khoản bị khóa",
                password_hash=get_password_hash("Password@123"),
                is_active=False,
                is_superuser=False,
            )
            session.add(inactive_user)
            await session.flush()
            await session.execute(
                user_roles.insert().values(user_id=inactive_user.id, role_id=mkt_role.id)
            )

            # 5. Seed Demo Categories and 10 Products from PLAN.md
            await seed_demo_categories_and_products(session, admin_user_id=admin_user.id)

            # 6. Seed Demo Inventory Batches and Movements
            await seed_demo_inventory(session, admin_user_id=admin_user.id)

            # 7. Seed Demo Promotions
            await seed_demo_promotions(session, admin_user_id=admin_user.id)

            # 8. Seed Demo Campaigns
            await seed_demo_campaigns(session, admin_user_id=admin_user.id)

            # 9. Seed Demo Content Items
            await seed_demo_content_items(session, admin_user_id=admin_user.id)

            # 10. Seed Demo Analytics & Attribution
            await seed_demo_analytics_and_attribution(session, admin_user_id=admin_user.id)

            # 11. Seed Demo Automations
            await seed_demo_automations(session, admin_user_id=admin_user.id)

            # 12. Seed Demo Recommendations & Alerts
            await seed_demo_recommendations_and_alerts(session)

            # 13. Seed Demo Social Connections & Publishing
            await seed_demo_social_publishing(session)

            # 14. Seed Demo AI Prompt Templates & Logs
            await seed_demo_ai_templates(session)

            await session.commit()

    asyncio.run(init())


@pytest.fixture
def client():
    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_headers(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@mochhealthy.vn", "password": "Password@123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def marketing_headers(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "marketing@mochhealthy.vn", "password": "Password@123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def inventory_headers(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "inventory@mochhealthy.vn", "password": "Password@123"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

