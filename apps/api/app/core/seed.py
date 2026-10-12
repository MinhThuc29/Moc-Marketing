import logging
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.auth import Role, Permission, User, role_permissions
from app.models.product import Category, Product, PriceAuditLog, ProductStatus
from app.models.social import SocialConnection, PublishedPost, PostMetric, SocialPlatform, ConnectionStatus, PublishStatus
from app.models.ai import PromptTemplate, AIGenerationLog, PromptCategory, AILogStatus
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

ALL_PERMISSIONS = [
    ("product.read", "Xem danh sách và chi tiết sản phẩm"),
    ("product.write", "Tạo, sửa, cập nhật trạng thái và giá sản phẩm"),
    ("inventory.read", "Xem tồn kho theo lô và hạn sử dụng"),
    ("inventory.write", "Nhập kho, điều chỉnh số lượng và ghi nhận xuất kho"),
    ("order.read", "Xem danh sách và chi tiết đơn hàng đa kênh"),
    ("order.update", "Cập nhật trạng thái đơn hàng và ghi chú vận hành"),
    ("customer.read", "Xem dữ liệu khách hàng và Customer 360"),
    ("campaign.create", "Tạo chiến dịch marketing mới"),
    ("campaign.approve", "Duyệt chiến dịch marketing và ngân sách"),
    ("content.create", "Tạo và chỉnh sửa nội dung bài đăng / kịch bản"),
    ("content.approve", "Phê duyệt nội dung tiếp thị trước khi đăng"),
    ("content.publish", "Xuất bản bài đăng lên các kênh mạng xã hội"),
    ("analytics.read", "Xem báo cáo doanh thu, chuyển đổi và phân bổ marketing"),
    ("settings.manage", "Cấu hình hệ thống, kho hàng và kết nối bên ngoài"),
    ("user.manage", "Quản lý người dùng, phân quyền và tài khoản nhân viên"),
]

ROLE_PERMISSIONS_MAP = {
    "ADMIN": [p[0] for p in ALL_PERMISSIONS],
    "OWNER": [p[0] for p in ALL_PERMISSIONS],
    "MARKETING": [
        "product.read",
        "customer.read",
        "campaign.create",
        "campaign.approve",
        "content.create",
        "content.approve",
        "content.publish",
        "analytics.read",
    ],
    "SALES": [
        "product.read",
        "customer.read",
        "order.read",
        "order.update",
    ],
    "INVENTORY": [
        "product.read",
        "inventory.read",
        "inventory.write",
    ],
}


DEMO_CATEGORIES = [
    {
        "name": "Trái cây tươi",
        "slug": "trai-cay-tuoi",
        "description": "Trái cây tuyển chọn tươi sạch, cắt sẵn đóng hộp tiện lợi",
        "sort_order": 1,
        "active": True,
    },
    {
        "name": "Nước ép nguyên chất",
        "slug": "nuoc-ep-nguyen-chat",
        "description": "Nước ép ép chậm 100% nguyên chất, không thêm đường nước",
        "sort_order": 2,
        "active": True,
    },
    {
        "name": "Sinh tố & Đồ uống đá xay",
        "slug": "sinh-to-do-uong-da-xay",
        "description": "Sinh tố kết hợp trái cây tươi và sữa tươi dinh dưỡng",
        "sort_order": 3,
        "active": True,
    },
    {
        "name": "Sữa chua hoa quả",
        "slug": "sua-chua-hoa-qua",
        "description": "Sữa chua lên men tự nhiên kết hợp sốt hoa quả tươi",
        "sort_order": 4,
        "active": True,
    },
    {
        "name": "Trà & Matcha thanh nhiệt",
        "slug": "tra-matcha-thanh-nhiet",
        "description": "Trà thảo mộc và matcha nguyên chất mát lành bổ dưỡng",
        "sort_order": 5,
        "active": True,
    },
]

DEMO_PRODUCTS = [
    {
        "sku": "FRUIT-TAO-NZ",
        "slug": "tao-new-zealand-gion-ngot",
        "name": "Táo New Zealand giòn ngọt",
        "short_description": "Táo New Zealand nhập khẩu giòn ngọt, rửa sạch cắt sẵn tiện dụng",
        "description": "Táo New Zealand tuyển chọn loại 1, bảo quản lạnh ở nhiệt độ tiêu chuẩn để giữ trọn vẹn độ giòn xốp và vitamin.",
        "category_slug": "trai-cay-tuoi",
        "base_price": 49000.0,
        "sale_price": None,
        "cost_price": 25000.0,
        "unit": "hộp",
        "status": ProductStatus.ACTIVE.value,
        "featured": True,
        "tags": ["organic", "fresh", "apple", "nhap-khau"],
        "ingredients": "100% Táo New Zealand tươi",
        "allergens": None,
        "nutrition_text": "Năng lượng: ~95 kcal, Chất xơ: 4.4g, Vitamin C: 8.4mg",
        "preparation_note": "Rửa sạch bằng nước ozone, gọt vỏ và cắt lát đóng hộp vô trùng",
        "storage_note": "Bảo quản ngăn mát tủ lạnh (2-6°C)",
        "shelf_life": "2 ngày kể từ ngày đóng hộp",
        "thumbnail": "/images/products/tao-nz.jpg",
        "media": ["/images/products/tao-nz.jpg", "/images/products/tao-nz-detail.jpg"],
        "seo_title": "Táo New Zealand giòn ngọt cắt sẵn | Mộc Healthy",
        "seo_description": "Mua táo New Zealand giòn ngọt tươi ngon cắt sẵn giao nhanh tại Mộc Healthy.",
    },
    {
        "sku": "FRUIT-THANH-LONG",
        "slug": "thanh-long-trang-do",
        "name": "Thanh long trắng/đỏ",
        "short_description": "Thanh long Bình Thuận tươi mát, giàu chất chống oxy hóa",
        "description": "Thanh long ruột đỏ và ruột trắng phối hợp, cắt miếng vừa ăn đóng hộp vệ sinh an toàn thực phẩm.",
        "category_slug": "trai-cay-tuoi",
        "base_price": 32000.0,
        "sale_price": None,
        "cost_price": 15000.0,
        "unit": "hộp",
        "status": ProductStatus.ACTIVE.value,
        "featured": False,
        "tags": ["fresh", "dragonfruit", "vitamin", "thanh-nhiet"],
        "ingredients": "100% Thanh long tươi sạch",
        "allergens": None,
        "nutrition_text": "Năng lượng: ~60 kcal, Vitamin C, Chất xơ",
        "preparation_note": "Cắt khối vừa ăn đóng hộp nắp đậy kín",
        "storage_note": "Bảo quản ngăn mát 2-6°C",
        "shelf_life": "24-48 giờ",
        "thumbnail": "/images/products/thanh-long.jpg",
        "media": ["/images/products/thanh-long.jpg"],
        "seo_title": "Thanh long trắng đỏ đóng hộp | Mộc Healthy",
        "seo_description": "Thanh long trắng đỏ tươi ngọt mọng nước, giàu chất xơ và vitamin C.",
    },
    {
        "sku": "FRUIT-DUA-LUOI",
        "slug": "dua-luoi-vang",
        "name": "Dưa lưới vàng",
        "short_description": "Dưa lưới ruột cam giòn ngọt đậm vị, giàu vitamin A",
        "description": "Dưa lưới công nghệ cao chuẩn VietGAP, vị ngọt thanh tự nhiên, giòn tan trong miệng.",
        "category_slug": "trai-cay-tuoi",
        "base_price": 49000.0,
        "sale_price": None,
        "cost_price": 26000.0,
        "unit": "hộp",
        "status": ProductStatus.ACTIVE.value,
        "featured": False,
        "tags": ["fresh", "melon", "vietgap", "ngot-thanh"],
        "ingredients": "100% Dưa lưới vàng VietGAP",
        "allergens": None,
        "nutrition_text": "Năng lượng: ~55 kcal, Vitamin A, Vitamin C",
        "preparation_note": "Gọt vỏ bỏ hạt cắt lát mỏng vừa ăn",
        "storage_note": "Bảo quản lạnh 2-6°C",
        "shelf_life": "2 ngày",
        "thumbnail": "/images/products/dua-luoi.jpg",
        "media": ["/images/products/dua-luoi.jpg"],
        "seo_title": "Dưa lưới vàng VietGAP giòn ngọt | Mộc Healthy",
        "seo_description": "Dưa lưới vàng tươi giòn ngọt đậm vị bổ dưỡng tại Mộc Healthy.",
    },
    {
        "sku": "JUICE-THOM-TAO",
        "slug": "nuoc-ep-thom-tao",
        "name": "Nước ép thơm táo",
        "short_description": "Nước ép táo và thơm nguyên chất ép chậm giữ trọn enzyme",
        "description": "Sự kết hợp hoàn hảo giữa vị ngọt thanh của táo New Zealand và vị chua dịu của thơm giúp thanh lọc cơ thể.",
        "category_slug": "nuoc-ep-nguyen-chat",
        "base_price": 30000.0,
        "sale_price": None,
        "cost_price": 14000.0,
        "unit": "chai",
        "status": ProductStatus.ACTIVE.value,
        "featured": False,
        "tags": ["coldpressed", "juice", "detox", "no-sugar"],
        "ingredients": "Táo 60%, Dứa/Thơm 40%",
        "allergens": None,
        "nutrition_text": "Năng lượng: ~120 kcal, Vitamin C, Enzyme Bromelain",
        "preparation_note": "Ép chậm công nghệ thủy lực lạnh, không thêm đường hay nước",
        "storage_note": "Giữ lạnh liên tục 2-4°C, lắc đều trước khi uống",
        "shelf_life": "24 giờ (khuyên dùng trong ngày)",
        "thumbnail": "/images/products/nuoc-ep-thom-tao.jpg",
        "media": ["/images/products/nuoc-ep-thom-tao.jpg"],
        "seo_title": "Nước ép thơm táo ép chậm nguyên chất | Mộc Healthy",
        "seo_description": "Nước ép thơm táo detox cơ thể 100% tự nhiên không đường tại Mộc Healthy.",
    },
    {
        "sku": "SMOOTH-BO",
        "slug": "sinh-to-bo",
        "name": "Sinh tố bơ",
        "short_description": "Bơ sáp Đắk Lắk dẻo béo xay mịn cùng sữa tươi dinh dưỡng",
        "description": "Bơ sáp chín tự nhiên, xay sánh mịn chuẩn vị healthy béo thơm bổ dưỡng.",
        "category_slug": "sinh-to-do-uong-da-xay",
        "base_price": 35000.0,
        "sale_price": None,
        "cost_price": 18000.0,
        "unit": "ly",
        "status": ProductStatus.ACTIVE.value,
        "featured": True,
        "tags": ["avocado", "smoothie", "healthy-fat", "bestseller"],
        "ingredients": "Bơ sáp Đắk Lắk, sữa tươi tiệt trùng, sữa chua ít đường",
        "allergens": "Sữa bò",
        "nutrition_text": "Năng lượng: ~280 kcal, Chất béo tốt OMEGA-3, Kali",
        "preparation_note": "Xay mịn cùng đá tuyết tinh khiết",
        "storage_note": "Dùng lạnh ngay sau khi pha chế",
        "shelf_life": "Nên dùng ngay trong vòng 2 giờ",
        "thumbnail": "/images/products/sinh-to-bo.jpg",
        "media": ["/images/products/sinh-to-bo.jpg"],
        "seo_title": "Sinh tố bơ sáp Đắk Lắk béo ngậy | Mộc Healthy",
        "seo_description": "Sinh tố bơ tươi dinh dưỡng dẻo sánh thơm ngon tại Mộc Healthy.",
    },
    {
        "sku": "YOGURT-DAU",
        "slug": "sua-chua-dau",
        "name": "Sữa chua dâu",
        "short_description": "Sữa chua Hy Lạp mix dâu tây Đà Lạt tươi mát chua ngọt",
        "description": "Dâu tây tươi sấy dẻo và sốt dâu tươi nhà làm hòa quyện trên nền sữa chua men sống.",
        "category_slug": "sua-chua-hoa-qua",
        "base_price": 33000.0,
        "sale_price": None,
        "cost_price": 16000.0,
        "unit": "hũ",
        "status": ProductStatus.ACTIVE.value,
        "featured": False,
        "tags": ["yogurt", "strawberry", "probiotic", "healthy-snack"],
        "ingredients": "Sữa chua lên men, dâu tây Đà Lạt, mật ong nguyên chất",
        "allergens": "Sữa bò",
        "nutrition_text": "Năng lượng: ~140 kcal, Probiotics, Protein 6g",
        "preparation_note": "Trộn sốt dâu tây tươi tự nấu ít ngọt",
        "storage_note": "Bảo quản lạnh 2-6°C",
        "shelf_life": "3 ngày",
        "thumbnail": "/images/products/sua-chua-dau.jpg",
        "media": ["/images/products/sua-chua-dau.jpg"],
        "seo_title": "Sữa chua dâu tây Đà Lạt tươi ngon | Mộc Healthy",
        "seo_description": "Sữa chua hoa quả dâu tây chua ngọt mát lạnh hỗ trợ tiêu hóa.",
    },
    {
        "sku": "YOGURT-XOAI",
        "slug": "sua-chua-xoai",
        "name": "Sữa chua xoài",
        "short_description": "Sữa chua thơm ngon kèm topping xoài Cát Chu ngọt lịm",
        "description": "Vị chua thanh mát của sữa chua kết hợp cùng xoài Cát Chu chín vàng mọng nước.",
        "category_slug": "sua-chua-hoa-qua",
        "base_price": 32000.0,
        "sale_price": None,
        "cost_price": 15000.0,
        "unit": "hũ",
        "status": ProductStatus.ACTIVE.value,
        "featured": False,
        "tags": ["yogurt", "mango", "probiotic", "dessert"],
        "ingredients": "Sữa chua men sống, xoài Cát Chu cắt hạt lựu",
        "allergens": "Sữa bò",
        "nutrition_text": "Năng lượng: ~135 kcal, Vitamin A, Canxi",
        "preparation_note": "Topping xoài tươi hạt lựu tự nhiên",
        "storage_note": "Bảo quản lạnh 2-6°C",
        "shelf_life": "3 ngày",
        "thumbnail": "/images/products/sua-chua-xoai.jpg",
        "media": ["/images/products/sua-chua-xoai.jpg"],
        "seo_title": "Sữa chua xoài Cát Chu thanh mát | Mộc Healthy",
        "seo_description": "Sữa chua hoa quả xoài Cát Chu chín mọng giải nhiệt ngày hè.",
    },
    {
        "sku": "JUICE-CAM",
        "slug": "nuoc-ep-cam",
        "name": "Nước ép cam",
        "short_description": "Cam sành mọng nước vắt tươi nguyên chất 100% giàu vitamin C",
        "description": "Cam tươi thu hoạch trong ngày vắt lấy nước tự nhiên, tăng cường đề kháng.",
        "category_slug": "nuoc-ep-nguyen-chat",
        "base_price": 20000.0,
        "sale_price": None,
        "cost_price": 9000.0,
        "unit": "chai",
        "status": ProductStatus.ACTIVE.value,
        "featured": False,
        "tags": ["orange", "vitaminc", "fresh-juice", "immunity"],
        "ingredients": "100% Nước cốt cam sành tươi",
        "allergens": None,
        "nutrition_text": "Năng lượng: ~90 kcal, Vitamin C: 60mg",
        "preparation_note": "Vắt cơ học vệ sinh, không đắng vỏ",
        "storage_note": "Bảo quản mát 2-4°C, uống ngay sau khi mở nắp",
        "shelf_life": "12-24 giờ",
        "thumbnail": "/images/products/nuoc-ep-cam.jpg",
        "media": ["/images/products/nuoc-ep-cam.jpg"],
        "seo_title": "Nước cam vắt tươi nguyên chất 100% | Mộc Healthy",
        "seo_description": "Nước ép cam tươi bổ sung đề kháng giá tốt mỗi ngày tại Mộc Healthy.",
    },
    {
        "sku": "TEA-MATCHA",
        "slug": "matcha-latte",
        "name": "Matcha latte",
        "short_description": "Bột trà xanh Uji Nhật Bản hòa quyện cùng sữa tươi thanh trùng",
        "description": "Matcha thượng hạng giữ nguyên vị đậm đà kết hợp sữa tươi tạo nên thức uống tỉnh táo êm dịu.",
        "category_slug": "tra-matcha-thanh-nhiet",
        "base_price": 35000.0,
        "sale_price": None,
        "cost_price": 17000.0,
        "unit": "ly",
        "status": ProductStatus.ACTIVE.value,
        "featured": False,
        "tags": ["matcha", "latte", "japan", "antioxidant"],
        "ingredients": "Bột trà xanh matcha Uji, sữa tươi thanh trùng",
        "allergens": "Sữa bò",
        "nutrition_text": "Năng lượng: ~150 kcal, EGCG chống oxy hóa",
        "preparation_note": "Đánh bọt chasen truyền thống",
        "storage_note": "Dùng lạnh kèm đá",
        "shelf_life": "Dùng ngon nhất trong 1 giờ",
        "thumbnail": "/images/products/matcha-latte.jpg",
        "media": ["/images/products/matcha-latte.jpg"],
        "seo_title": "Matcha Latte Uji Nhật Bản đậm vị | Mộc Healthy",
        "seo_description": "Matcha Latte trà xanh nguyên chất Uji thơm béo tỉnh táo mỗi sáng.",
    },
    {
        "sku": "TEA-TRA-DAU",
        "slug": "tra-dau-tay",
        "name": "Trà dâu tây",
        "short_description": "Trà lài ủ lạnh thơm ngát kết hợp mứt dâu tây tươi và dâu tươi cắt lát",
        "description": "Thức uống best seller tại Mộc Healthy. Trà lài hảo hạng kết hợp dâu tây tươi mát lạnh thanh nhiệt mùa hè.",
        "category_slug": "tra-matcha-thanh-nhiet",
        "base_price": 30000.0,
        "sale_price": 25000.0,  # Promo price per PLAN.md Section 6.1
        "cost_price": 13000.0,
        "unit": "ly",
        "status": ProductStatus.ACTIVE.value,
        "featured": True,
        "tags": ["tea", "strawberry", "bestseller", "promo", "signature"],
        "ingredients": "Cốt trà lài, sốt dâu tây tươi, dâu tây lát, đường phèn tự nhiên",
        "allergens": None,
        "nutrition_text": "Năng lượng: ~110 kcal, Vitamin C",
        "preparation_note": "Lắc đều cùng đá và dâu tây tươi cắt lát",
        "storage_note": "Dùng lạnh",
        "shelf_life": "Dùng ngon nhất trong 2 giờ",
        "thumbnail": "/images/products/tra-dau-tay.jpg",
        "media": ["/images/products/tra-dau-tay.jpg"],
        "seo_title": "Trà dâu tây tươi mát lạnh Best Seller | Mộc Healthy",
        "seo_description": "Trà dâu tây giải nhiệt thơm ngon giá ưu đãi chỉ 25k tại Mộc Healthy.",
    },
]


async def seed_roles_and_permissions(db: AsyncSession) -> None:
    """
    Seeds initial permissions, roles, and role-permission mappings idempotently.
    """
    # 1. Seed Permissions
    permissions_dict = {}
    for perm_name, perm_desc in ALL_PERMISSIONS:
        result = await db.execute(select(Permission).where(Permission.name == perm_name))
        perm = result.scalar_one_or_none()
        if not perm:
            perm = Permission(name=perm_name, description=perm_desc)
            db.add(perm)
            await db.flush()
        permissions_dict[perm_name] = perm

    # 2. Seed Roles and map permissions via table insertion
    for role_name, allowed_perms in ROLE_PERMISSIONS_MAP.items():
        result = await db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=role_name, description=f"Vai trò vận hành {role_name}")
            db.add(role)
            await db.flush()

        # Clear existing role_permissions and re-insert
        await db.execute(delete(role_permissions).where(role_permissions.c.role_id == role.id))
        for p_name in allowed_perms:
            if p_name in permissions_dict:
                await db.execute(
                    role_permissions.insert().values(
                        role_id=role.id,
                        permission_id=permissions_dict[p_name].id,
                    )
                )

    await db.commit()
    logger.info("Roles and permissions seeded successfully.")


async def seed_demo_categories_and_products(db: AsyncSession, admin_user_id: str = None) -> None:
    """
    Seeds the 5 categories and 10 demo products from PLAN.md Section 6.1 idempotently.
    """
    # 1. Categories
    category_map = {}
    for cat_data in DEMO_CATEGORIES:
        res = await db.execute(select(Category).where(Category.slug == cat_data["slug"]))
        cat = res.scalar_one_or_none()
        if not cat:
            cat = Category(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                sort_order=cat_data["sort_order"],
                active=cat_data["active"],
            )
            db.add(cat)
            await db.flush()
        category_map[cat_data["slug"]] = cat

    # 2. Products
    for p_data in DEMO_PRODUCTS:
        res = await db.execute(select(Product).where(Product.sku == p_data["sku"]))
        prod = res.scalar_one_or_none()
        cat = category_map.get(p_data["category_slug"])
        cat_id = cat.id if cat else None

        if not prod:
            prod = Product(
                sku=p_data["sku"],
                slug=p_data["slug"],
                name=p_data["name"],
                short_description=p_data["short_description"],
                description=p_data["description"],
                category_id=cat_id,
                base_price=p_data["base_price"],
                sale_price=p_data["sale_price"],
                cost_price=p_data["cost_price"],
                unit=p_data["unit"],
                status=p_data["status"],
                featured=p_data["featured"],
                tags=p_data["tags"],
                ingredients=p_data["ingredients"],
                allergens=p_data["allergens"],
                nutrition_text=p_data["nutrition_text"],
                preparation_note=p_data["preparation_note"],
                storage_note=p_data["storage_note"],
                shelf_life=p_data["shelf_life"],
                thumbnail=p_data["thumbnail"],
                media=p_data["media"],
                seo_title=p_data["seo_title"],
                seo_description=p_data["seo_description"],
            )
            db.add(prod)
            await db.flush()

            # Seed initial price audit log
            audit = PriceAuditLog(
                product_id=prod.id,
                old_base_price=None,
                new_base_price=p_data["base_price"],
                old_sale_price=None,
                new_sale_price=p_data["sale_price"],
                changed_by_user_id=admin_user_id,
                change_reason="Khởi tạo giá sản phẩm demo ban đầu",
            )
            db.add(audit)

    await db.commit()
    logger.info("Demo categories and 10 products seeded successfully.")


async def seed_demo_inventory(db: AsyncSession, admin_user_id: str = None) -> None:
    """
    Seeds demo batches and movements for F&B products idempotently.
    Includes normal batches, critical expiring batches (<24h), warning batches (<=3 days),
    and expired batches to test FEFO and alerts.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.inventory import InventoryBatch, InventoryMovement, BatchStatus, MovementType

    res_batch_count = await db.execute(select(func.count(InventoryBatch.id)))
    if (res_batch_count.scalar() or 0) > 0:
        return

    now = datetime.now(timezone.utc)
    res_prods = await db.execute(select(Product))
    products = {p.sku: p for p in res_prods.scalars().all()}

    if not products:
        return

    demo_batch_configs = [
        # 1. Táo NZ - 2 batches (1 warning, 1 fresh)
        {
            "sku": "FRUIT-TAO-NZ",
            "code": "BATCH-TAO-001",
            "received_qty": 40,
            "available_qty": 28,
            "expiry": now + timedelta(days=2),
            "supplier": "Nông trại Xanh Đà Lạt",
            "cost": 25000.0,
        },
        {
            "sku": "FRUIT-TAO-NZ",
            "code": "BATCH-TAO-002",
            "received_qty": 50,
            "available_qty": 50,
            "expiry": now + timedelta(days=5),
            "supplier": "Công ty NK Hoa Quả Sạch",
            "cost": 25000.0,
        },
        # 2. Bưởi Da Xanh - 1 critical (< 16h), 1 warning (1.5 days)
        {
            "sku": "FRUIT-BUOI-DAXANH",
            "code": "BATCH-BUOI-CRIT",
            "received_qty": 30,
            "available_qty": 14,
            "expiry": now + timedelta(hours=14),
            "supplier": "Hợp tác xã Bến Tre",
            "cost": 28000.0,
        },
        {
            "sku": "FRUIT-BUOI-DAXANH",
            "code": "BATCH-BUOI-002",
            "received_qty": 35,
            "available_qty": 35,
            "expiry": now + timedelta(days=2),
            "supplier": "Hợp tác xã Bến Tre",
            "cost": 28000.0,
        },
        # 3. Nước ép cần tây táo xanh - 1 critical (< 10h), 1 fresh (24h)
        {
            "sku": "JUICE-CAN-TAY-TAO",
            "code": "BATCH-CANTAY-001",
            "received_qty": 25,
            "available_qty": 8,
            "expiry": now + timedelta(hours=9),
            "supplier": "Bếp trung tâm Mộc Healthy",
            "cost": 22000.0,
        },
        {
            "sku": "JUICE-CAN-TAY-TAO",
            "code": "BATCH-CANTAY-002",
            "received_qty": 30,
            "available_qty": 30,
            "expiry": now + timedelta(days=1),
            "supplier": "Bếp trung tâm Mộc Healthy",
            "cost": 22000.0,
        },
        # 4. Nước ép cam cà rốt
        {
            "sku": "JUICE-CAM-CA-ROT",
            "code": "BATCH-CAMCAROT-001",
            "received_qty": 20,
            "available_qty": 18,
            "expiry": now + timedelta(days=2),
            "supplier": "Bếp trung tâm Mộc Healthy",
            "cost": 20000.0,
        },
        # 5. Thanh Long - Low stock (5 hộp < 10)
        {
            "sku": "FRUIT-THANH-LONG",
            "code": "BATCH-TL-LOW",
            "received_qty": 20,
            "available_qty": 4,
            "expiry": now + timedelta(days=2),
            "supplier": "Nhà vườn Chợ Gạo",
            "cost": 15000.0,
        },
        # 6. Sữa chua hy lạp - Expired batch demo (quá hạn 8h)
        {
            "sku": "YOGURT-HY-LAP-BERRY",
            "code": "BATCH-YOG-EXPIRED",
            "received_qty": 15,
            "available_qty": 3,
            "expiry": now - timedelta(hours=8),
            "supplier": "Lò sữa Ba Vì",
            "cost": 29000.0,
        },
        {
            "sku": "YOGURT-HY-LAP-BERRY",
            "code": "BATCH-YOG-FRESH",
            "received_qty": 25,
            "available_qty": 25,
            "expiry": now + timedelta(days=6),
            "supplier": "Lò sữa Ba Vì",
            "cost": 29000.0,
        },
    ]

    for cfg in demo_batch_configs:
        prod = products.get(cfg["sku"])
        if not prod:
            continue

        batch = InventoryBatch(
            product_id=prod.id,
            batch_code=cfg["code"],
            quantity_received=cfg["received_qty"],
            quantity_available=cfg["available_qty"],
            cost_per_unit=cfg["cost"],
            supplier=cfg["supplier"],
            received_at=now - timedelta(days=1),
            expiry_at=cfg["expiry"],
            status=BatchStatus.ACTIVE.value,
            note="Lô hàng ban đầu demo hệ thống",
            created_at=now - timedelta(days=1),
            updated_at=now,
        )
        db.add(batch)
        await db.flush()

        # Log purchase_in movement
        m_in = InventoryMovement(
            batch_id=batch.id,
            product_id=prod.id,
            movement_type=MovementType.PURCHASE_IN.value,
            quantity=cfg["received_qty"],
            previous_quantity=0,
            new_quantity=cfg["received_qty"],
            reason="Nhập kho ban đầu",
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=1),
        )
        db.add(m_in)

        # If available < received, log sale_out movement to balance
        sold_qty = cfg["received_qty"] - cfg["available_qty"]
        if sold_qty > 0:
            m_out = InventoryMovement(
                batch_id=batch.id,
                product_id=prod.id,
                movement_type=MovementType.SALE_OUT.value,
                quantity=sold_qty,
                previous_quantity=cfg["received_qty"],
                new_quantity=cfg["available_qty"],
                reference_id="DEMO-SALE-001",
                reason="Xuất bán demo tại quầy",
                created_by_user_id=admin_user_id,
                created_at=now - timedelta(hours=6),
            )
            db.add(m_out)

    await db.commit()
    logger.info("Demo inventory batches and movements seeded successfully.")


async def seed_demo_promotions(db: AsyncSession, admin_user_id: str = None) -> None:
    """
    Seeds demo promotions and vouchers idempotently according to PLAN.md Section 8.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.promotion import Promotion, PromotionType, PromotionStatus, ProductScope, CustomerScope

    res_count = await db.execute(select(func.count(Promotion.id)))
    if (res_count.scalar() or 0) > 0:
        return

    now = datetime.now(timezone.utc)
    res_prods = await db.execute(select(Product))
    products = {p.sku: p for p in res_prods.scalars().all()}

    demo_promos = [
        # 1. Voucher chào bạn mới 20%
        Promotion(
            title="Ưu Đãi Bạn Mới 20% Đơn Đầu Tiên",
            code="WELCOME20",
            description="Giảm 20% tối đa 40.000đ cho đơn hàng từ 100.000đ",
            type=PromotionType.PERCENT_DISCOUNT.value,
            value=20.0,
            min_order_value=100000.0,
            max_discount=40000.0,
            start_at=now - timedelta(days=5),
            end_at=now + timedelta(days=30),
            product_scope=ProductScope.ALL.value,
            customer_scope=CustomerScope.NEW_CUSTOMER.value,
            usage_limit=500,
            usage_count=12,
            usage_per_customer=1,
            stackable=False,
            status=PromotionStatus.ACTIVE.value,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=5),
            updated_at=now,
        ),
        # 2. Miễn phí vận chuyển FREESHIP
        Promotion(
            title="Miễn Phí Vận Chuyển Toàn Thành Phố",
            code="FREESHIP",
            description="Freeship tối đa 30.000đ cho đơn hàng từ 120.000đ",
            type=PromotionType.FREE_SHIPPING.value,
            value=30000.0,
            min_order_value=120000.0,
            max_discount=30000.0,
            start_at=now - timedelta(days=10),
            end_at=now + timedelta(days=60),
            product_scope=ProductScope.ALL.value,
            customer_scope=CustomerScope.ALL.value,
            usage_limit=1000,
            usage_count=45,
            usage_per_customer=3,
            stackable=True,
            status=PromotionStatus.ACTIVE.value,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=10),
            updated_at=now,
        ),
        # 3. Flash Sale Nước Ép 25% (Auto apply không cần mã)
        Promotion(
            title="Flash Sale Nước Ép Tươi Mát Giải Nhiệt 25%",
            code=None,
            description="Tự động giảm 25% các sản phẩm nước ép cần tây và cam cà rốt",
            type=PromotionType.FLASH_SALE.value,
            value=25.0,
            min_order_value=0.0,
            max_discount=50000.0,
            start_at=now - timedelta(hours=6),
            end_at=now + timedelta(hours=18),
            product_scope=ProductScope.SPECIFIC_PRODUCTS.value,
            applicable_product_ids=[
                p.id for p in products.values() if "JUICE" in p.sku
            ],
            customer_scope=CustomerScope.ALL.value,
            usage_limit=None,
            usage_count=8,
            usage_per_customer=5,
            stackable=False,
            status=PromotionStatus.ACTIVE.value,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(hours=6),
            updated_at=now,
        ),
        # 4. Giảm cố định 30K HEALTHY30K
        Promotion(
            title="Voucher Giảm 30K Tri Ân Khách Hàng",
            code="HEALTHY30K",
            description="Giảm ngay 30.000đ cho đơn hàng từ 180.000đ",
            type=PromotionType.FIXED_DISCOUNT.value,
            value=30000.0,
            min_order_value=180000.0,
            max_discount=30000.0,
            start_at=now - timedelta(days=2),
            end_at=now + timedelta(days=20),
            product_scope=ProductScope.ALL.value,
            customer_scope=CustomerScope.ALL.value,
            usage_limit=200,
            usage_count=19,
            usage_per_customer=1,
            stackable=False,
            status=PromotionStatus.ACTIVE.value,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=2),
            updated_at=now,
        ),
        # 5. Mua 2 tặng 1 cho Táo New Zealand
        Promotion(
            title="Mua 2 Tặng 1 Táo New Zealand Cắt Sẵn",
            code="MUA2TANG1",
            description="Mua 2 hộp táo New Zealand tặng ngay 1 hộp miễn phí",
            type=PromotionType.BUY_X_GET_Y.value,
            value=49000.0,
            min_order_value=0.0,
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
            product_scope=ProductScope.SPECIFIC_PRODUCTS.value,
            applicable_product_ids=[
                products["FRUIT-TAO-NZ"].id
            ] if "FRUIT-TAO-NZ" in products else [],
            buy_x_get_y_config={"buy_quantity": 2, "get_quantity": 1},
            customer_scope=CustomerScope.ALL.value,
            usage_limit=100,
            usage_count=5,
            usage_per_customer=2,
            stackable=False,
            status=PromotionStatus.ACTIVE.value,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=1),
            updated_at=now,
        ),
    ]

    for promo in demo_promos:
        db.add(promo)

    await db.commit()
    logger.info("Demo promotions seeded successfully.")


async def seed_demo_campaigns(db: AsyncSession, admin_user_id: str = None) -> None:
    """
    Seeds demo marketing campaigns idempotently according to PLAN.md Section 12.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.campaign import Campaign, CampaignChannel, CampaignProduct, CampaignObjective, CampaignStatus
    from app.models.promotion import Promotion

    res_count = await db.execute(select(func.count(Campaign.id)))
    if (res_count.scalar() or 0) > 0:
        return

    now = datetime.now(timezone.utc)
    res_prods = await db.execute(select(Product))
    products = list(res_prods.scalars().all())
    prod_map = {p.sku: p for p in products}

    res_promo = await db.execute(select(Promotion).limit(2))
    promos = list(res_promo.scalars().all())
    promo_id_1 = promos[0].id if promos else None
    promo_id_2 = promos[1].id if len(promos) > 1 else None

    c1 = Campaign(
        name="Chiến dịch Năng Lượng Xanh Mùa Thu",
        code="CAMP-DETOX-OCT26",
        objective=CampaignObjective.CONVERSION.value,
        status=CampaignStatus.ACTIVE.value,
        start_at=now - timedelta(days=5),
        end_at=now + timedelta(days=20),
        budget=12000000.0,
        actual_spend=8500000.0,
        revenue_attributed=28400000.0,
        target_audience=["ACTIVE", "REPEAT", "VIP"],
        promotion_id=promo_id_1,
        landing_page="https://mochanh.vn/collections/autumn-green",
        utm_source="facebook",
        utm_medium="cpc",
        utm_campaign="autumn_green",
        notes="Chiến dịch trọng điểm tháng 10 đẩy mạnh dòng sữa hạt mè đen và nước ép cần tây",
        created_by_user_id=admin_user_id,
        approved_by_user_id=admin_user_id,
        approved_at=now - timedelta(days=6),
        created_at=now - timedelta(days=7),
    )
    db.add(c1)
    await db.flush()

    c1_channels = [
        CampaignChannel(campaign_id=c1.id, channel="FACEBOOK", channel_budget=5000000.0, channel_spend=3800000.0, target_metric="300 conversions", notes="Facebook Ads Newsfeed"),
        CampaignChannel(campaign_id=c1.id, channel="TIKTOK", channel_budget=4000000.0, channel_spend=3200000.0, target_metric="80k views, 150 đơn", notes="TikTok Creator Ads"),
        CampaignChannel(campaign_id=c1.id, channel="ZALO", channel_budget=3000000.0, channel_spend=1500000.0, target_metric="100 Zalo OA orders", notes="ZNS thông báo ưu đãi"),
    ]
    for ch in c1_channels:
        db.add(ch)

    if products:
        c1_prods = [
            CampaignProduct(campaign_id=c1.id, product_id=products[0].id, is_hero_product=True, special_price=45000.0),
        ]
        if len(products) > 1:
            c1_prods.append(CampaignProduct(campaign_id=c1.id, product_id=products[1].id, is_hero_product=False, special_price=52000.0))
        for pr in c1_prods:
            db.add(pr)

    c2 = Campaign(
        name="Xả Kho Trái Cây Tươi Cận Date",
        code="CAMP-CLEARANCE-OCT",
        objective=CampaignObjective.CLEARANCE.value,
        status=CampaignStatus.ACTIVE.value,
        start_at=now - timedelta(days=2),
        end_at=now + timedelta(days=3),
        budget=3000000.0,
        actual_spend=2100000.0,
        revenue_attributed=9800000.0,
        target_audience=["REPEAT", "AT_RISK"],
        promotion_id=promo_id_2,
        landing_page="https://mochanh.vn/collections/flash-sale",
        utm_source="zalo",
        utm_medium="broadcast",
        utm_campaign="clearance_oct",
        notes="Giải phóng tồn kho lô trái cây cắt sẵn bảo quản 3 ngày",
        created_by_user_id=admin_user_id,
        approved_by_user_id=admin_user_id,
        approved_at=now - timedelta(days=2),
        created_at=now - timedelta(days=3),
    )
    db.add(c2)
    await db.flush()

    c2_channels = [
        CampaignChannel(campaign_id=c2.id, channel="ZALO", channel_budget=2000000.0, channel_spend=1600000.0, target_metric="Zalo OA broadcast push", notes="Gửi tin Broadcast Zalo"),
        CampaignChannel(campaign_id=c2.id, channel="SMS", channel_budget=1000000.0, channel_spend=500000.0, target_metric="SMS Brandname 1500 tin", notes="Khách hàng cũ trong bán kính 3km"),
    ]
    for ch in c2_channels:
        db.add(ch)

    c3 = Campaign(
        name="Tri Ân Khách Hàng Thân Thiết & VIP Q4",
        code="CAMP-VIP-THANKS",
        objective=CampaignObjective.LOYALTY.value,
        status=CampaignStatus.READY_FOR_REVIEW.value,
        start_at=now + timedelta(days=3),
        end_at=now + timedelta(days=25),
        budget=15000000.0,
        actual_spend=0.0,
        revenue_attributed=0.0,
        target_audience=["VIP", "HIGH_VALUE"],
        landing_page="https://mochanh.vn/vip-rewards",
        utm_source="email",
        utm_medium="crm",
        utm_campaign="vip_thanks",
        notes="Tặng voucher sinh nhật và quà tặng hộp hạt dinh dưỡng cao cấp",
        created_by_user_id=admin_user_id,
        created_at=now - timedelta(days=1),
    )
    db.add(c3)
    await db.flush()

    c3_channels = [
        CampaignChannel(campaign_id=c3.id, channel="EMAIL", channel_budget=3000000.0, target_metric="Open rate > 40%", notes="Email marketing cá nhân hóa"),
        CampaignChannel(campaign_id=c3.id, channel="ZALO", channel_budget=7000000.0, target_metric="Zalo ZNS CSKH VIP", notes="Zalo 1-1 chăm sóc khách"),
        CampaignChannel(campaign_id=c3.id, channel="SMS", channel_budget=5000000.0, target_metric="Tặng mã voucher riêng", notes="SMS Voucher VIP"),
    ]
    for ch in c3_channels:
        db.add(ch)

    c4 = Campaign(
        name="Ra Mắt Set Salad Mùa Lễ Hội 2026",
        code="CAMP-NEW-SALAD",
        objective=CampaignObjective.AWARENESS.value,
        status=CampaignStatus.APPROVED.value,
        start_at=now + timedelta(days=7),
        end_at=now + timedelta(days=30),
        budget=8000000.0,
        actual_spend=0.0,
        revenue_attributed=0.0,
        target_audience=["NEW", "ACTIVE"],
        landing_page="https://mochanh.vn/new-menu",
        utm_source="instagram",
        utm_medium="social",
        utm_campaign="holiday_salad",
        notes="Ra mắt 3 vị salad ức gà sốt mè rang và sốt chanh leo",
        created_by_user_id=admin_user_id,
        approved_by_user_id=admin_user_id,
        approved_at=now,
        created_at=now - timedelta(days=2),
    )
    db.add(c4)
    await db.flush()

    c4_channels = [
        CampaignChannel(campaign_id=c4.id, channel="INSTAGRAM", channel_budget=4000000.0, target_metric="30k reach", notes="Hình ảnh món ăn phong cách Minimalist"),
        CampaignChannel(campaign_id=c4.id, channel="WEBSITE_BANNER", channel_budget=1000000.0, target_metric="Banner hero trang chủ", notes="Top banner storefront"),
        CampaignChannel(campaign_id=c4.id, channel="TIKTOK", channel_budget=3000000.0, target_metric="Viral short videos", notes="Video review mukbang healthy"),
    ]
    for ch in c4_channels:
        db.add(ch)

    await db.commit()
    logger.info("Demo marketing campaigns seeded successfully.")


async def seed_demo_content_items(db: AsyncSession, admin_user_id: str | None = None) -> None:
    """Seed sample marketing content items across multiple social channels and lifecycle states."""
    from datetime import datetime, timezone, timedelta
    from app.models.content import (
        ContentItem,
        ContentType,
        ContentChannel,
        ContentStatus,
        BrandTone,
    )
    from app.models.product import Product
    from app.models.campaign import Campaign

    # 1. Check if content items already exist
    count_res = await db.execute(select(func.count(ContentItem.id)))
    if count_res.scalar_one() > 0:
        logger.info("Content items already seeded, skipping.")
        return

    now = datetime.now(timezone.utc)

    # 2. Get sample product and campaign for association
    res_prod = await db.execute(select(Product).limit(3))
    demo_products = res_prod.scalars().all()
    p1 = demo_products[0] if len(demo_products) > 0 else None
    p2 = demo_products[1] if len(demo_products) > 1 else None

    res_camp = await db.execute(select(Campaign).limit(2))
    demo_camps = res_camp.scalars().all()
    c1 = demo_camps[0] if len(demo_camps) > 0 else None
    c2 = demo_camps[1] if len(demo_camps) > 1 else None

    items = [
        # 1. Facebook Published Post
        ContentItem(
            title="[Facebook] Bữa sáng 5 phút tràn đầy năng lượng cùng Táo New Zealand & Granola",
            content_type=ContentType.FACEBOOK_POST.value,
            channel=ContentChannel.FACEBOOK.value,
            status=ContentStatus.PUBLISHED.value,
            brand_tone=BrandTone.FRESH_ENERGETIC.value,
            hook="⏰ 7h sáng và bạn chỉ có 5 phút trước khi đến văn phòng? Đừng bỏ bữa sáng nữa!",
            body=(
                "Một bát sữa chua Hy Lạp mát lành, rắc thêm một nắm Granola giòn rụm và vài lát táo New Zealand tươi ngọt từ Mộc Healthy...\n\n"
                "✅ Đủ chất xơ, vitamin và đạm thực vật duy trì năng lượng\n"
                "✅ No lâu êm bụng, tỉnh táo làm việc suốt cả buổi sáng\n"
                "✅ 100% nguyên liệu tự nhiên không đường hóa học độc hại.\n\n"
                "Chỉ mất đúng 3 phút chuẩn bị là bạn đã có ngay một bữa sáng chuẩn Eat Clean tại gia!"
            ),
            cta="Nhắn tin cho Mộc hoặc ghé thăm mochanh.vn để đặt combo ăn sáng healthy giảm ngay 20k hôm nay!",
            hashtags=["#MocHealthy", "#EatCleanVietNam", "#BuaSangHealthy", "#GranolaGionRum", "#SongKhoeMoiNgay"],
            product_id=p1.id if p1 else None,
            campaign_id=c1.id if c1 else None,
            external_post_id="fb_post_8839210",
            external_post_url="https://facebook.com/mochealthy/posts/fb_post_8839210",
            metrics={"likes": 245, "comments": 42, "shares": 18, "reach": 4680, "clicks": 312},
            created_by_user_id=admin_user_id,
            approved_by_user_id=admin_user_id,
            approved_at=now - timedelta(days=3),
            published_at=now - timedelta(days=2),
            created_at=now - timedelta(days=4),
        ),

        # 2. TikTok Scheduled Script
        ContentItem(
            title="[TikTok 45s] Thử thách 7 ngày thanh lọc cơ thể với Nước ép cần tây Mộc Healthy",
            content_type=ContentType.TIKTOK_SCRIPT.value,
            channel=ContentChannel.TIKTOK.value,
            status=ContentStatus.SCHEDULED.value,
            brand_tone=BrandTone.TRENDY_HUMOR.value,
            hook="Uống nước ép cần tây có thực sự kinh khủng như lời đồn? Xem biểu cảm của mình ngày 1 và ngày 7 nè!",
            body=(
                "👉 0-3s: Cận cảnh chai nước ép xanh ngắt mát lạnh rót ra ly đá kêu lách cách bắt tai.\n"
                "👉 4-15s: Uống ngụm đầu tiên - bất ngờ vì vị táo và dưa leo làm dịu hoàn toàn vị hăng của cần tây, ngọt thanh tự nhiên!\n"
                "👉 16-30s: Nhật ký ngày thứ 3 và ngày thứ 7: Da dẻ mịn màng, bụng nhẹ tênh không còn đầy hơi.\n"
                "👉 31-45s: Chia sẻ bí quyết ép chậm công nghệ cold-pressed giữ trọn 98% enzyme thực vật."
            ),
            cta="Nhấp vào giỏ hàng góc trái video để đặt set 6 chai ép chậm với voucher freeship nhé!",
            hashtags=["#MocHealthy", "#NuocEpCanTay", "#Detox7Ngay", "#TrendingTikTok", "#AnSachSongKhoe"],
            product_id=p2.id if p2 else None,
            campaign_id=c1.id if c1 else None,
            scheduled_at=now + timedelta(days=1, hours=4),
            created_by_user_id=admin_user_id,
            approved_by_user_id=admin_user_id,
            approved_at=now - timedelta(hours=6),
            created_at=now - timedelta(days=1),
        ),

        # 3. Zalo OA Message In Review
        ContentItem(
            title="[Zalo OA] Gửi tặng bạn mã giảm giá 15% cho tuần làm việc mới rạng rỡ",
            content_type=ContentType.ZALO_MESSAGE.value,
            channel=ContentChannel.ZALO.value,
            status=ContentStatus.IN_REVIEW.value,
            brand_tone=BrandTone.WARM_FRIENDLY.value,
            hook="Chào bạn, đầu tuần này bạn đã nạp đủ vitamin và khoáng chất cho cơ thể chưa?",
            body=(
                "Mộc Healthy thương gửi bạn mã ưu đãi MOCLAMDEP giảm ngay 15% cho tất cả đơn hàng nước ép nguyên chất và salad hoa quả tươi trong hôm nay.\n\n"
                "🎁 Đặc biệt: Đơn từ 199k được tặng kèm 1 hũ sữa chua Hy Lạp sốt việt quất thủ công.\n\n"
                "Bảo quản tươi mới trong ngày, giao nhanh tận bàn làm việc trong 30-45 phút!"
            ),
            cta="Nhấn nút 'ĐẶT MÓN NGAY' bên dưới để nhận ưu đãi trước 23h59 hôm nay!",
            hashtags=["#MocHealthy", "#UuDaiDauTuan", "#ZaloOA", "#ChamSocKhachHang"],
            campaign_id=c2.id if c2 else None,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(hours=5),
        ),

        # 4. Instagram Reel AI Generated Draft
        ContentItem(
            title="[Reel 30s] ASMR Chuẩn bị hộp salad rau củ hữu cơ sắc màu",
            content_type=ContentType.REEL_SCRIPT.value,
            channel=ContentChannel.INSTAGRAM.value,
            status=ContentStatus.AI_GENERATED.value,
            brand_tone=BrandTone.MINIMAL_HEALTHY.value,
            hook="Âm thanh giòn tan của xà lách tươi và sốt mè rang béo ngậy... Bạn có thèm không?",
            body=(
                "🎬 Phân cảnh 1: Cắt xà lách xoăn xanh mướt (ASMR tiếng dao thớt gỗ mộc mạc).\n"
                "🎬 Phân cảnh 2: Xếp cà chua bi đỏ mọng, ngô ngọt và ức gà nướng xé sợi.\n"
                "🎬 Phân cảnh 3: Rưới dòng sốt mè rang óng ánh phủ đều mặt hộp."
            ),
            cta="Lưu lại video này để tự làm hoặc đặt ngay tại Mộc Healthy chỉ 49k!",
            hashtags=["#MocHealthy", "#SaladASMR", "#HealthyLunch", "#MinimalistFood", "#EatClean"],
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(hours=12),
        ),

        # 5. Website Banner Copy Draft
        ContentItem(
            title="[Banner Hero] Mùa thu sống xanh - Thanh lọc cùng Mộc Healthy",
            content_type=ContentType.WEBSITE_BANNER_COPY.value,
            channel=ContentChannel.WEBSITE_BANNER.value,
            status=ContentStatus.DRAFT.value,
            brand_tone=BrandTone.NUTRITION_EXPERT.value,
            hook="100% Nguyên liệu Hữu cơ chuẩn VietGAP — Tươi sạch mỗi ngày từ nông trại đến bàn ăn.",
            body="Khám phá bộ sưu tập đồ ăn kiêng và nước ép thanh lọc được các chuyên gia dinh dưỡng cân chỉnh calo chuẩn xác.",
            cta="KHÁM PHÁ THỰC ĐƠN MỚI",
            hashtags=["#MocHealthy", "#VietGAP", "#DinhDuongChuanKhoaHoc"],
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=1),
        ),

        # 6. Facebook Post Approved Ready to Publish
        ContentItem(
            title="[Facebook] Sự thật về lượng đường trong nước ép đóng chai vs ép chậm nguyên chất",
            content_type=ContentType.FACEBOOK_POST.value,
            channel=ContentChannel.FACEBOOK.value,
            status=ContentStatus.APPROVED.value,
            brand_tone=BrandTone.NUTRITION_EXPERT.value,
            hook="Bạn có biết 1 chai nước ép công nghiệp có thể chứa đến 8 thìa đường cát?",
            body=(
                "Hôm nay, hãy cùng chuyên gia dinh dưỡng của Mộc Healthy làm rõ vì sao nước ép tươi ép chậm lại là giải pháp tối ưu:\n\n"
                "1️⃣ Giữ nguyên vitamin và chất chống oxy hóa nhờ công nghệ ép không sinh nhiệt.\n"
                "2️⃣ Không pha thêm dù chỉ 1 giọt nước hay đường tinh luyện.\n"
                "3️⃣ Hấp thu êm ái mà không làm tăng vọt chỉ số đường huyết trong máu."
            ),
            cta="Bình luận 'TƯ VẤN' để nhận thực đơn ép chậm phù hợp với thể trạng của bạn!",
            hashtags=["#MocHealthy", "#DinhDuongSach", "#NuocEpCham", "#SucKhoeMoiNgay"],
            product_id=p2.id if p2 else None,
            created_by_user_id=admin_user_id,
            approved_by_user_id=admin_user_id,
            approved_at=now - timedelta(hours=2),
            created_at=now - timedelta(hours=8),
        ),
    ]

    for it in items:
        db.add(it)

    await db.commit()
    logger.info("Demo marketing content items seeded successfully (%d items).", len(items))


async def seed_demo_analytics_and_attribution(db: AsyncSession, admin_user_id: str | None = None) -> None:
    """Seed tracking clickstream events and conversion attribution records."""
    from datetime import datetime, timezone, timedelta
    from app.models.analytics import (
        TrackingEvent,
        ConversionAttribution,
        AttributionModel,
        AttributionConfidence,
    )
    from app.models.order import Order
    from app.models.campaign import Campaign
    from app.models.content import ContentItem

    # 1. Check if attributions already seeded
    res_count = await db.execute(select(func.count(ConversionAttribution.id)))
    if res_count.scalar_one() > 0:
        logger.info("Analytics and conversion attributions already seeded, skipping.")
        return

    now = datetime.now(timezone.utc)

    # 2. Query campaigns, orders, and content items
    res_camp = await db.execute(select(Campaign).limit(4))
    camps = res_camp.scalars().all()
    c1 = camps[0] if len(camps) > 0 else None
    c2 = camps[1] if len(camps) > 1 else None

    res_orders = await db.execute(select(Order).limit(8))
    orders = res_orders.scalars().all()

    res_content = await db.execute(select(ContentItem).limit(3))
    content_list = res_content.scalars().all()
    ct1 = content_list[0] if len(content_list) > 0 else None

    # 3. Create sample clickstream tracking events
    events: list[TrackingEvent] = []
    channels_sample = [
        ("FACEBOOK", "facebook", "cpc", "autumn_green", "ad_feed_01"),
        ("TIKTOK", "tiktok", "video", "detox_7days", "asmr_review"),
        ("ZALO", "zalo", "broadcast", "vip_october", "oa_message"),
        ("INSTAGRAM", "instagram", "social", "salad_fest", "reel_story"),
        ("GOOGLE", "google", "organic", "healthy_food", "seo"),
    ]

    for i in range(25):
        ch_info = channels_sample[i % len(channels_sample)]
        event_time = now - timedelta(days=20 - (i % 20), hours=i % 24)
        ev = TrackingEvent(
            event_name="page_view" if i % 4 == 0 else "product_view" if i % 4 == 1 else "add_to_cart" if i % 4 == 2 else "campaign_click",
            anonymous_id=f"anon_seed_user_{i % 8}",
            session_id=f"sess_seed_{i % 12}",
            channel=ch_info[0],
            utm_source=ch_info[1],
            utm_medium=ch_info[2],
            utm_campaign=ch_info[3],
            utm_content=ch_info[4],
            campaign_id=c1.id if (i % 2 == 0 and c1) else (c2.id if c2 else None),
            content_id=ct1.id if (i % 3 == 0 and ct1) else None,
            created_at=event_time,
            event_metadata={"device": "mobile" if i % 2 == 0 else "desktop"},
        )
        events.append(ev)

    for ev in events:
        db.add(ev)
    await db.flush()

    # 4. Create conversion attributions for existing orders
    attributions: list[ConversionAttribution] = []
    for idx, ord in enumerate(orders):
        order_rev = float(ord.total_amount)
        assigned_camp = c1 if idx % 2 == 0 else c2
        is_direct = (idx % 3 == 0)

        camp_id = None if is_direct else (assigned_camp.id if assigned_camp else None)
        camp_code = None if is_direct else (assigned_camp.code if assigned_camp else None)
        conf = AttributionConfidence.UNKNOWN.value if is_direct else AttributionConfidence.DETERMINISTIC.value if ord.channel == "WEBSITE" else AttributionConfidence.INFERRED.value

        first_src = "direct / none" if is_direct else f"{assigned_camp.utm_source or 'facebook'} / {assigned_camp.utm_medium or 'cpc'}" if assigned_camp else "social / organic"
        last_src = first_src

        # First Touch
        attributions.append(
            ConversionAttribution(
                order_id=ord.id,
                order_number=ord.order_number,
                attribution_model=AttributionModel.FIRST_TOUCH.value,
                confidence=conf,
                first_touch_source=first_src,
                last_touch_source=last_src,
                campaign_id=camp_id,
                campaign_code=camp_code,
                touchpoints_count=2 if not is_direct else 1,
                order_revenue=order_rev,
                attributed_revenue=0.0 if is_direct else order_rev,
                attribution_weight=1.0,
                touchpoint_details=[{"channel": ord.channel, "source": first_src}],
                created_at=ord.created_at,
            )
        )

        # Last Touch
        attributions.append(
            ConversionAttribution(
                order_id=ord.id,
                order_number=ord.order_number,
                attribution_model=AttributionModel.LAST_TOUCH.value,
                confidence=conf,
                first_touch_source=first_src,
                last_touch_source=last_src,
                campaign_id=camp_id,
                campaign_code=camp_code,
                touchpoints_count=2 if not is_direct else 1,
                order_revenue=order_rev,
                attributed_revenue=0.0 if is_direct else order_rev,
                attribution_weight=1.0,
                touchpoint_details=[{"channel": ord.channel, "source": last_src}],
                created_at=ord.created_at,
            )
        )

        # Linear
        attributions.append(
            ConversionAttribution(
                order_id=ord.id,
                order_number=ord.order_number,
                attribution_model=AttributionModel.LINEAR.value,
                confidence=conf,
                first_touch_source=first_src,
                last_touch_source=last_src,
                campaign_id=camp_id,
                campaign_code=camp_code,
                touchpoints_count=2 if not is_direct else 1,
                order_revenue=order_rev,
                attributed_revenue=0.0 if is_direct else order_rev,
                attribution_weight=1.0,
                touchpoint_details=[{"channel": ord.channel, "source": first_src}],
                created_at=ord.created_at,
            )
        )

    for attr in attributions:
        db.add(attr)

    await db.commit()
    logger.info("Demo tracking events (%d) and conversion attributions (%d) seeded successfully.", len(events), len(attributions))


async def seed_demo_automations(db: AsyncSession, admin_user_id: str | None = None) -> None:
    """
    Seeds initial production-ready Marketing Automation workflows and run logs
    according to PLAN.md Section 22 and Phase 7.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.automation import (
        AutomationWorkflow,
        AutomationRun,
        TriggerType,
        WorkflowStatus,
        RunStatus,
        ActionType,
    )

    res_count = await db.execute(select(func.count(AutomationWorkflow.id)))
    if res_count.scalar_one() > 0:
        logger.info("Automation workflows already seeded, skipping.")
        return

    now = datetime.now(timezone.utc)

    templates = [
        AutomationWorkflow(
            name="Chào đón thành viên mới & Tặng mã Welcome 20%",
            code="WF-WELCOME-01",
            description="Kích hoạt khi khách hàng mới đăng ký tài khoản. Kiểm tra có đồng ý nhận marketing, gửi tin nhắn Zalo OA chào mừng, tặng 10 điểm Mộc Xu và gửi mã giảm giá WELCOME20.",
            trigger_type=TriggerType.CUSTOMER_CREATED.value,
            trigger_config={"channel": "ONLINE", "welcome_delay_seconds": 60},
            conditions=[
                {"field": "consent_marketing", "operator": "eq", "value": True}
            ],
            actions=[
                {"type": ActionType.SEND_ZALO_MOCK.value, "template": "welcome_member", "message": "Chào mừng {customer_name} đến với Mộc Healthy! Tặng bạn 10 Mộc Xu và mã WELCOME20 giảm 20% đơn đầu tiên."},
                {"type": ActionType.ADD_LOYALTY_POINTS.value, "points": 10},
                {"type": ActionType.ISSUE_PROMOTION.value, "promotion_code": "WELCOME20"},
                {"type": ActionType.ADD_CUSTOMER_TAG.value, "tag": "welcome_engaged"},
            ],
            status=WorkflowStatus.ACTIVE.value,
            is_system_template=True,
            total_runs=18,
            successful_runs=18,
            failed_runs=0,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=7),
            updated_at=now - timedelta(days=1),
        ),
        AutomationWorkflow(
            name="Khôi phục giỏ hàng bị bỏ quên (Abandoned Cart Recovery)",
            code="WF-ABANDONED-CART-01",
            description="Kích hoạt khi giỏ hàng chưa thanh toán sau 2 giờ. Gửi tin nhắn Zalo nhắc nhở kèm mã FREESHIP miễn phí vận chuyển để tối ưu tỷ lệ hoàn tất đơn.",
            trigger_type=TriggerType.CART_ABANDONED.value,
            trigger_config={"inactive_hours": 2, "min_cart_value": 80000},
            conditions=[
                {"field": "cart_total", "operator": "gte", "value": 80000}
            ],
            actions=[
                {"type": ActionType.WAIT_HOURS.value, "wait_hours": 2},
                {"type": ActionType.SEND_ZALO_MOCK.value, "template": "abandoned_cart_reminder", "message": "Chào {customer_name}, bạn còn giỏ hàng trái cây tươi mát chưa thanh toán. Nhập ngay mã FREESHIP để được miễn phí giao hàng tận nơi nhé!"},
                {"type": ActionType.ISSUE_PROMOTION.value, "promotion_code": "FREESHIP"},
            ],
            status=WorkflowStatus.ACTIVE.value,
            is_system_template=True,
            total_runs=24,
            successful_runs=22,
            failed_runs=2,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=6),
            updated_at=now - timedelta(days=2),
        ),
        AutomationWorkflow(
            name="Chăm sóc sau mua & Gợi ý đặt hàng lặp lại (Repeat Purchase Flow)",
            code="WF-REPEAT-PURCHASE-01",
            description="Kích hoạt sau khi đơn hàng hoàn tất 3 ngày. Gửi tin nhắn khảo sát độ hài lòng món ăn và gợi ý combo nước ép dinh dưỡng cho tuần mới.",
            trigger_type=TriggerType.ORDER_COMPLETED.value,
            trigger_config={"wait_days": 3},
            conditions=[
                {"field": "order_total", "operator": "gte", "value": 100000}
            ],
            actions=[
                {"type": ActionType.WAIT_HOURS.value, "wait_hours": 72},
                {"type": ActionType.SEND_ZALO_MOCK.value, "template": "post_purchase_care", "message": "Mộc Healthy cảm ơn {customer_name} đã thưởng thức bữa ăn! Bạn cảm thấy món ăn thế nào? Đặt thêm nước ép nguyên chất cho ngày mới tràn đầy năng lượng nhé!"},
                {"type": ActionType.ADD_LOYALTY_POINTS.value, "points": 5},
            ],
            status=WorkflowStatus.ACTIVE.value,
            is_system_template=True,
            total_runs=15,
            successful_runs=15,
            failed_runs=0,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=1),
        ),
        AutomationWorkflow(
            name="Kích hoạt lại khách hàng có nguy cơ rời bỏ (At-Risk Reactivation)",
            code="WF-REACTIVATION-01",
            description="Kích hoạt khi khách hàng không phát sinh đơn trong 30 ngày (phân khúc AT_RISK hoặc DORMANT). Tự động gán nhãn cần chăm sóc và tặng voucher 30k HEALTHY30K.",
            trigger_type=TriggerType.CUSTOMER_INACTIVE.value,
            trigger_config={"inactive_days": 30},
            conditions=[
                {"field": "segment", "operator": "in", "value": ["AT_RISK", "DORMANT"]}
            ],
            actions=[
                {"type": ActionType.ADD_CUSTOMER_TAG.value, "tag": "cần_chăm_sóc_lại"},
                {"type": ActionType.SEND_ZALO_MOCK.value, "template": "reactivation_special", "message": "Mộc nhớ bạn {customer_name}! Đã lâu bạn chưa ghé quán. Mộc gửi tặng bạn voucher HEALTHY30K giảm ngay 30.000đ cho đơn tiếp theo nhé."},
                {"type": ActionType.ISSUE_PROMOTION.value, "promotion_code": "HEALTHY30K"},
            ],
            status=WorkflowStatus.ACTIVE.value,
            is_system_template=True,
            total_runs=9,
            successful_runs=9,
            failed_runs=0,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(days=1),
        ),
        AutomationWorkflow(
            name="Cảnh báo & Đề xuất xả kho lô hàng cận date (Inventory Clearance Alert)",
            code="WF-CLEARANCE-ALERT-01",
            description="Kích hoạt khi lô trái cây/nguyên liệu còn hạn dưới 3 ngày và tồn kho > 10 đơn vị. Tạo AI Recommendation và thông báo Owner để duyệt chiến dịch xả kho.",
            trigger_type=TriggerType.INVENTORY_EXPIRY_RISK.value,
            trigger_config={"days_to_expiry": 3, "min_quantity": 10},
            conditions=[
                {"field": "days_to_expiry", "operator": "lte", "value": 3},
                {"field": "quantity", "operator": "gte", "value": 10}
            ],
            actions=[
                {"type": ActionType.CREATE_NOTIFICATION.value, "notification_title": "Cảnh báo tồn kho cận date", "notification_body": "Lô hàng sắp hết hạn trong 3 ngày, cần kích hoạt chiến dịch giải phóng tồn kho."},
                {"type": ActionType.CREATE_RECOMMENDATION.value, "notification_title": "Đề xuất AI: Tạo Flash Sale xả kho trái cây cận date giảm 20-30%"},
                {"type": ActionType.CREATE_CAMPAIGN_DRAFT.value},
            ],
            status=WorkflowStatus.ACTIVE.value,
            is_system_template=True,
            total_runs=6,
            successful_runs=6,
            failed_runs=0,
            created_by_user_id=admin_user_id,
            created_at=now - timedelta(days=3),
            updated_at=now,
        ),
    ]

    for t in templates:
        db.add(t)

    await db.flush()

    # Seed sample execution runs
    runs = [
        AutomationRun(
            workflow_id=templates[0].id,
            trigger_type=TriggerType.CUSTOMER_CREATED.value,
            trigger_source_id="cust-demo-01",
            status=RunStatus.SUCCESS.value,
            started_at=now - timedelta(hours=2, minutes=15),
            completed_at=now - timedelta(hours=2, minutes=14),
            step_runs=[
                {"step_index": 1, "action_type": "SEND_ZALO_MOCK", "status": "SUCCESS", "output": {"recipient": "0912345678", "channel": "ZALO_OA", "status": "DELIVERED"}},
                {"step_index": 2, "action_type": "ADD_LOYALTY_POINTS", "status": "SUCCESS", "output": {"points_awarded": 10, "status": "AWARDED"}},
                {"step_index": 3, "action_type": "ISSUE_PROMOTION", "status": "SUCCESS", "output": {"promotion_code": "WELCOME20", "status": "ISSUED"}},
                {"step_index": 4, "action_type": "ADD_CUSTOMER_TAG", "status": "SUCCESS", "output": {"tag": "welcome_engaged", "status": "TAGGED"}},
            ],
            metadata_json={"customer_name": "Nguyễn Hoàng Minh", "phone": "0912345678"},
            created_at=now - timedelta(hours=2, minutes=15),
        ),
        AutomationRun(
            workflow_id=templates[1].id,
            trigger_type=TriggerType.CART_ABANDONED.value,
            trigger_source_id="cart-demo-02",
            status=RunStatus.SUCCESS.value,
            started_at=now - timedelta(hours=5),
            completed_at=now - timedelta(hours=4, minutes=58),
            step_runs=[
                {"step_index": 1, "action_type": "WAIT_HOURS", "status": "SUCCESS", "output": {"wait_hours": 2}},
                {"step_index": 2, "action_type": "SEND_ZALO_MOCK", "status": "SUCCESS", "output": {"recipient": "0987654321", "channel": "ZALO_OA", "status": "DELIVERED"}},
                {"step_index": 3, "action_type": "ISSUE_PROMOTION", "status": "SUCCESS", "output": {"promotion_code": "FREESHIP", "status": "ISSUED"}},
            ],
            metadata_json={"customer_name": "Lê Thị Thu", "cart_total": 125000},
            created_at=now - timedelta(hours=5),
        ),
        AutomationRun(
            workflow_id=templates[2].id,
            trigger_type=TriggerType.ORDER_COMPLETED.value,
            trigger_source_id="ord-demo-03",
            status=RunStatus.SUCCESS.value,
            started_at=now - timedelta(days=1, hours=3),
            completed_at=now - timedelta(days=1, hours=3),
            step_runs=[
                {"step_index": 1, "action_type": "WAIT_HOURS", "status": "SUCCESS", "output": {"wait_hours": 72}},
                {"step_index": 2, "action_type": "SEND_ZALO_MOCK", "status": "SUCCESS", "output": {"recipient": "0933221100", "channel": "ZALO_OA", "status": "DELIVERED"}},
                {"step_index": 3, "action_type": "ADD_LOYALTY_POINTS", "status": "SUCCESS", "output": {"points_awarded": 5, "status": "AWARDED"}},
            ],
            metadata_json={"customer_name": "Trần Văn An", "order_total": 165000},
            created_at=now - timedelta(days=1, hours=3),
        ),
        AutomationRun(
            workflow_id=templates[3].id,
            trigger_type=TriggerType.CUSTOMER_INACTIVE.value,
            trigger_source_id="cust-demo-04",
            status=RunStatus.SUCCESS.value,
            started_at=now - timedelta(days=2),
            completed_at=now - timedelta(days=2),
            step_runs=[
                {"step_index": 1, "action_type": "ADD_CUSTOMER_TAG", "status": "SUCCESS", "output": {"tag": "cần_chăm_sóc_lại", "status": "TAGGED"}},
                {"step_index": 2, "action_type": "SEND_ZALO_MOCK", "status": "SUCCESS", "output": {"recipient": "0909090909", "channel": "ZALO_OA", "status": "DELIVERED"}},
                {"step_index": 3, "action_type": "ISSUE_PROMOTION", "status": "SUCCESS", "output": {"promotion_code": "HEALTHY30K", "status": "ISSUED"}},
            ],
            metadata_json={"customer_name": "Vũ Hoàng My", "segment": "AT_RISK", "inactive_days": 35},
            created_at=now - timedelta(days=2),
        ),
        AutomationRun(
            workflow_id=templates[4].id,
            trigger_type=TriggerType.INVENTORY_EXPIRY_RISK.value,
            trigger_source_id="batch-demo-05",
            status=RunStatus.SUCCESS.value,
            started_at=now - timedelta(days=3),
            completed_at=now - timedelta(days=3),
            step_runs=[
                {"step_index": 1, "action_type": "CREATE_NOTIFICATION", "status": "SUCCESS", "output": {"title": "Cảnh báo tồn kho cận date", "status": "NOTIFIED"}},
                {"step_index": 2, "action_type": "CREATE_RECOMMENDATION", "status": "SUCCESS", "output": {"recommendation_title": "Đề xuất AI: Tạo Flash Sale", "status": "RECOMMENDATION_CREATED"}},
                {"step_index": 3, "action_type": "CREATE_CAMPAIGN_DRAFT", "status": "SUCCESS", "output": {"campaign_code": "CAMP-AUTO-1005", "status": "CAMPAIGN_DRAFT_CREATED"}},
            ],
            metadata_json={"batch_sku": "FRUIT-TAO-NZ", "days_to_expiry": 2, "quantity": 18},
            created_at=now - timedelta(days=3),
        ),
        AutomationRun(
            workflow_id=templates[1].id,
            trigger_type=TriggerType.CART_ABANDONED.value,
            trigger_source_id="cart-demo-06",
            status=RunStatus.FAILED.value,
            started_at=now - timedelta(days=4),
            completed_at=now - timedelta(days=4),
            step_runs=[
                {"step_index": 1, "action_type": "WAIT_HOURS", "status": "SUCCESS", "output": {"wait_hours": 2}},
                {"step_index": 2, "action_type": "SEND_ZALO_MOCK", "status": "FAILED", "error": "Zalo OA template 'abandoned_cart_reminder' quota rate limit exceeded (mock error)"},
            ],
            error_message="Zalo OA template 'abandoned_cart_reminder' quota rate limit exceeded",
            metadata_json={"customer_name": "Bùi Mai Hương", "cart_total": 95000},
            created_at=now - timedelta(days=4),
        ),
    ]

    for r in runs:
        db.add(r)

    await db.commit()
    logger.info("Demo automation workflows (%d) and execution runs (%d) seeded successfully.", len(templates), len(runs))


async def seed_demo_recommendations_and_alerts(db: AsyncSession) -> None:
    """
    Seed demo AI recommendations and operational smart alerts.
    """
    from app.models.recommendation import (
        AIRecommendation,
        SmartAlert,
        RecommendationType,
        RecommendationStatus,
        ConfidenceLevel,
        AlertSeverity,
        AlertStatus,
        AlertType,
    )

    existing_rec = await db.scalar(select(func.count(AIRecommendation.id)))
    if existing_rec and existing_rec > 0:
        logger.info("AI recommendations already seeded (%d records), skipping.", existing_rec)
        return

    now = datetime.now(timezone.utc)

    # 1. Demo AI Recommendations
    recs = [
        AIRecommendation(
            id=str(uuid.uuid4()),
            recommendation_type=RecommendationType.INVENTORY_CLEARANCE.value,
            status=RecommendationStatus.PENDING.value,
            title="Flash Sale giải cứu lô Táo New Zealand giòn ngọt cận date",
            problem_statement="Lô BATCH-TAO-01 còn 35 phần sắp chạm mốc hạn dùng trong 48h tới. Tốc độ bán tại quầy hiện tại chưa đủ để tiêu thụ hết trước hạn.",
            recommended_action="Tạo chiến dịch Flash Sale giảm 25% kèm quà tặng mini trên Website & Zalo OA, đồng thời tạo thông báo đẩy để kích cầu tiêu dùng nhanh trong ngày.",
            evidence=[
                {"metric": "Tồn kho cận date", "value": "35 phần (Lô: BATCH-TAO-01)", "comparison": "HSD còn 2 ngày (hết hạn 10/10)", "source": "inventory_batches"},
                {"metric": "Chi phí nguyên liệu có nguy cơ hủy", "value": "1.050.000đ", "comparison": "Nguy cơ mất 100% vốn nếu không xả hàng", "source": "inventory_batches"},
                {"metric": "Tốc độ bán trung bình", "value": "4 phần/ngày", "comparison": "Cần tăng tốc độ bán x4 trong 48h", "source": "orders"},
            ],
            target_products=[{"sku": "FRUIT-TAO-NZ", "name": "Táo New Zealand giòn ngọt", "base_price": 49000}],
            target_channels=["WEBSITE_BANNER", "ZALO"],
            suggested_promotion={
                "promo_type": "PERCENTAGE_DISCOUNT",
                "discount_value": 25,
                "code": "CLEARTAONZ",
                "min_order_value": 0,
            },
            expected_impact={
                "estimated_revenue": 1286000,
                "waste_prevented_units": 35,
                "capital_recovered": "75%",
            },
            confidence_score=0.92,
            confidence_level=ConfidenceLevel.HIGH.value,
            risks=[
                "Biên lợi nhuận gộp giảm từ 42% xuống 18% nhưng bảo toàn vốn nguyên liệu",
            ],
            created_at=now - timedelta(hours=4),
        ),
        AIRecommendation(
            id=str(uuid.uuid4()),
            recommendation_type=RecommendationType.CAMPAIGN_OPPORTUNITY.value,
            status=RecommendationStatus.PENDING.value,
            title="Đẩy mạnh chiến dịch video ngắn TikTok: Trà dâu tây tươi",
            problem_statement="Sản phẩm Trà dâu tây đang đạt tỷ lệ tăng trưởng đơn hàng cao nhất (+38% tuần này) nhưng chưa có chiến dịch phủ sóng mạng xã hội chuyên sâu.",
            recommended_action="Sử dụng AI Content Studio tạo gói kịch bản video TikTok 45s và bài viết Facebook hướng tới giới văn phòng giải nhiệt buổi chiều, tặng kèm voucher FREESHIP.",
            evidence=[
                {"metric": "Tăng trưởng doanh số tuần", "value": "+38.5% WoW", "comparison": "Sản phẩm tăng trưởng nhanh nhất tuần", "source": "analytics"},
                {"metric": "Lượt tương tác clickstream", "value": "184 lượt xem sản phẩm", "comparison": "Tỷ lệ thêm giỏ hàng đạt 24.1%", "source": "tracking_events"},
                {"metric": "Nguyên liệu trong kho", "value": "Đầy đủ dâu tây tươi và hồng trà", "comparison": "Đủ nguồn cung tăng gấp 2 lần đơn", "source": "inventory_batches"},
            ],
            target_products=[{"sku": "TEA-DAU-TAY", "name": "Trà dâu tây tươi", "base_price": 30000}],
            target_channels=["TIKTOK", "FACEBOOK", "ZALO"],
            suggested_promotion={
                "promo_type": "FREE_SHIPPING",
                "min_order_value": 80000,
                "code": "FREESHIPDAU",
            },
            expected_impact={
                "estimated_revenue": 4200000,
                "new_customer_reach": 420,
                "target_roas": 4.1,
            },
            confidence_score=0.88,
            confidence_level=ConfidenceLevel.HIGH.value,
            risks=[
                "Cần chuẩn bị đủ đá viên và ly mang đi vào các khung giờ vàng 14:00 - 16:00",
            ],
            created_at=now - timedelta(hours=8),
        ),
        AIRecommendation(
            id=str(uuid.uuid4()),
            recommendation_type=RecommendationType.CUSTOMER_RETENTION.value,
            status=RecommendationStatus.PENDING.value,
            title="Kích hoạt hành trình chăm sóc khách hàng ngủ đông qua Zalo OA",
            problem_statement="Có 8 khách hàng thân thiết thuộc phân khúc AT_RISK / DORMANT đã hơn 30 ngày không quay lại đặt món healthy.",
            recommended_action="Kích hoạt workflow tự động gửi tin nhắn Zalo OA 'Mộc Healthy Nhớ Bạn' tặng mã voucher độc quyền HEALTHY30K cho đơn từ 80k.",
            evidence=[
                {"metric": "Quy mô khách hàng AT_RISK", "value": "8 khách hàng", "comparison": "Không phát sinh đơn mới > 30 ngày", "source": "customers (RFM)"},
                {"metric": "AOV trung bình trong quá khứ", "value": "125.000đ/đơn", "comparison": "Từng có tần suất mua 2-3 lần/tuần", "source": "orders"},
                {"metric": "Chi phí tiếp cận lại", "value": "~15.000đ/khách", "comparison": "Rẻ hơn 70% so với tìm khách hàng mới", "source": "analytics"},
            ],
            target_customer_segment="AT_RISK",
            target_channels=["ZALO"],
            suggested_promotion={
                "promo_type": "FIXED_DISCOUNT",
                "discount_value": 30000,
                "min_order_value": 80000,
                "code": "HEALTHY30K",
            },
            expected_impact={
                "estimated_revenue": 1850000,
                "reactivation_rate": "22%",
            },
            confidence_score=0.84,
            confidence_level=ConfidenceLevel.HIGH.value,
            risks=[
                "Chỉ gửi 1 lần/tuần để đảm bảo trải nghiệm khách hàng",
            ],
            created_at=now - timedelta(days=1),
        ),
        AIRecommendation(
            id=str(uuid.uuid4()),
            recommendation_type=RecommendationType.CHANNEL_OPTIMIZATION.value,
            status=RecommendationStatus.PENDING.value,
            title="Chiến dịch điều hướng khách GrabFood/ShopeeFood về Kênh Website Trực Tiếp",
            problem_statement="Phí hoa hồng sàn 20-25% đang làm giảm biên lợi nhuận ròng của các dòng sinh tố và nước ép chỉ còn ~14%.",
            recommended_action="Kèm thiệp cảm ơn có mã QR trong mỗi đơn giao sàn, tặng ngay 10 Mộc Xu và ưu đãi 15% cho đơn đầu tiên trên Website.",
            evidence=[
                {"metric": "Hoa hồng sàn bên thứ 3", "value": "22.5% doanh thu", "comparison": "Lấy đi gần 1/4 giá trị mỗi ly nước", "source": "marketplace_imports"},
                {"metric": "Biên lợi nhuận kênh Website", "value": "39.2% Net Margin", "comparison": "Cao hơn gấp 2.8 lần so với bán qua sàn", "source": "analytics channel pnl"},
                {"metric": "Tỷ lệ khách hàng mua lại", "value": "35% có thói quen uống hàng ngày", "comparison": "Dễ dàng chuyển đổi sang kênh trực tiếp", "source": "customers"},
            ],
            target_channels=["WEBSITE_BANNER", "ZALO"],
            suggested_promotion={
                "promo_type": "PERCENTAGE_DISCOUNT",
                "discount_value": 15,
                "code": "MOCDIRECT",
            },
            expected_impact={
                "margin_improvement": "+14.0% biên lợi nhuận ròng",
                "customer_data": "Thu thập 100% SĐT khách hàng",
            },
            confidence_score=0.79,
            confidence_level=ConfidenceLevel.MEDIUM.value,
            risks=[
                "Cần thời gian in ấn bao bì thiệp cảm ơn gửi kèm",
            ],
            created_at=now - timedelta(days=2),
        ),
    ]

    for rec in recs:
        db.add(rec)

    # 2. Demo Smart Alerts
    alerts = [
        SmartAlert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.EXPIRY_RISK.value,
            severity=AlertSeverity.CRITICAL.value,
            status=AlertStatus.ACTIVE.value,
            title="Lô Táo New Zealand cận date (< 2 ngày)",
            message="Lô hàng BATCH-TAO-01 còn 35 phần sắp hết hạn vào ngày 10/10. Cần tạo Flash Sale xả hàng ngay!",
            entity_type="INVENTORY_BATCH",
            entity_id="batch-demo-tao-01",
            metric_data={"days_left": 2, "quantity_available": 35},
            action_url="/ai-studio",
            created_at=now - timedelta(hours=2),
        ),
        SmartAlert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.LOW_STOCK.value,
            severity=AlertSeverity.WARNING.value,
            status=AlertStatus.ACTIVE.value,
            title="Dưa lưới vàng sắp hết hàng (Tồn: 5 quả)",
            message="Tồn kho thực tế của Dưa lưới vàng đã chạm ngưỡng tối thiểu (ngưỡng: 10 quả). Hãy lên kế hoạch nhập hàng tươi mới.",
            entity_type="PRODUCT",
            entity_id="prod-dua-luoi",
            metric_data={"current_stock": 5, "threshold": 10},
            action_url="/inventory",
            created_at=now - timedelta(hours=5),
        ),
        SmartAlert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.LOW_MARGIN_RISK.value,
            severity=AlertSeverity.WARNING.value,
            status=AlertStatus.ACTIVE.value,
            title="Chiết khấu phí sàn GrabFood cao (>22%)",
            message="Phí hoa hồng và chiết khấu sàn tuần này chiếm 22.8% doanh thu. Khuyến nghị điều hướng đơn về Website hoặc Zalo OA.",
            entity_type="CHANNEL",
            entity_id="GRABFOOD",
            metric_data={"avg_commission": 0.228, "net_margin": 0.138},
            action_url="/analytics",
            created_at=now - timedelta(days=1),
        ),
        SmartAlert(
            id=str(uuid.uuid4()),
            alert_type=AlertType.REVENUE_ANOMALY.value,
            severity=AlertSeverity.INFO.value,
            status=AlertStatus.ACTIVE.value,
            title="Doanh thu kênh Website tăng trưởng ấn tượng (+42%)",
            message="Kênh bán trực tiếp Website ghi nhận doanh số tăng 42% so với trung bình 3 tuần trước nhờ chiến dịch Trà dâu tây.",
            entity_type="CHANNEL",
            entity_id="WEBSITE",
            metric_data={"growth_rate": 0.42, "current_revenue": 12500000},
            action_url="/analytics",
            created_at=now - timedelta(days=1, hours=10),
        ),
    ]

    for alert in alerts:
        db.add(alert)

    await db.commit()
    logger.info("Demo AI recommendations (%d) and smart alerts (%d) seeded successfully.", len(recs), len(alerts))


async def seed_demo_social_publishing(db: AsyncSession) -> None:
    """
    Seed demo Social Connections, Published Posts, and Post Metrics.
    """
    from app.models.social import (
        SocialConnection,
        PublishedPost,
        PostMetric,
        SocialPlatform,
        ConnectionStatus,
        PublishStatus,
    )
    from app.models.content import ContentItem

    existing_conn = await db.scalar(select(func.count(SocialConnection.id)))
    if existing_conn and existing_conn > 0:
        logger.info("Social connections already seeded (%d records), skipping.", existing_conn)
        return

    now = datetime.now(timezone.utc)

    # 1. Seed 5 Social Connections
    connections = [
        SocialConnection(
            id=str(uuid.uuid4()),
            platform=SocialPlatform.FACEBOOK.value,
            account_name="Mộc Healthy Farm Fanpage",
            account_id="fb_page_mochealthy_01",
            app_id="fb_app_mochealthy_prod",
            access_token="mock_fb_access_token_valid_eaab...",
            refresh_token="mock_fb_refresh_token_...",
            token_expires_at=now + timedelta(days=60),
            is_connected=True,
            status=ConnectionStatus.CONNECTED.value,
            is_mock=True,
            metadata_json={
                "category": "Organic Food & Beverages",
                "followers_count": 18450,
                "verified": True,
                "page_url": "https://facebook.com/mochealthy",
                "avatar_url": "/images/social/fb-avatar.png",
            },
            created_at=now - timedelta(days=30),
        ),
        SocialConnection(
            id=str(uuid.uuid4()),
            platform=SocialPlatform.INSTAGRAM.value,
            account_name="@moc.healthy.farm",
            account_id="ig_mochealthy_01",
            app_id="ig_app_mochealthy_prod",
            access_token="mock_ig_access_token_valid_...",
            token_expires_at=now + timedelta(days=45),
            is_connected=True,
            status=ConnectionStatus.CONNECTED.value,
            is_mock=True,
            metadata_json={
                "followers_count": 9200,
                "posts_count": 142,
                "profile_url": "https://instagram.com/moc.healthy.farm",
                "avatar_url": "/images/social/ig-avatar.png",
            },
            created_at=now - timedelta(days=25),
        ),
        SocialConnection(
            id=str(uuid.uuid4()),
            platform=SocialPlatform.TIKTOK.value,
            account_name="@moc_healthy_food",
            account_id="tt_mochealthy_01",
            app_id="tt_app_mochealthy_prod",
            access_token="mock_tt_access_token_valid_...",
            token_expires_at=now + timedelta(days=75),
            is_connected=True,
            status=ConnectionStatus.CONNECTED.value,
            is_mock=True,
            metadata_json={
                "followers_count": 34100,
                "likes_count": 185000,
                "profile_url": "https://tiktok.com/@moc_healthy_food",
                "avatar_url": "/images/social/tt-avatar.png",
            },
            created_at=now - timedelta(days=20),
        ),
        SocialConnection(
            id=str(uuid.uuid4()),
            platform=SocialPlatform.ZALO_OA.value,
            account_name="Mộc Healthy Official Account",
            account_id="zalo_oa_mochealthy_01",
            app_id="zalo_app_mochealthy_prod",
            access_token="mock_zalo_access_token_valid_...",
            token_expires_at=now + timedelta(days=30),
            is_connected=True,
            status=ConnectionStatus.CONNECTED.value,
            is_mock=True,
            metadata_json={
                "oa_type": "Doanh nghiệp",
                "followers_count": 5800,
                "oa_url": "https://oa.zalo.me/mochealthy",
                "avatar_url": "/images/social/zalo-avatar.png",
            },
            created_at=now - timedelta(days=15),
        ),
        SocialConnection(
            id=str(uuid.uuid4()),
            platform=SocialPlatform.WEBSITE_BLOG.value,
            account_name="Mộc Healthy Storefront Blog",
            account_id="web_blog_mochealthy_01",
            access_token="internal_api_key_system",
            token_expires_at=now + timedelta(days=365),
            is_connected=True,
            status=ConnectionStatus.CONNECTED.value,
            is_mock=True,
            metadata_json={
                "cms_type": "Storefront Built-in Engine",
                "domain": "https://mochealthy.vn",
                "active": True,
            },
            created_at=now - timedelta(days=40),
        ),
    ]

    for c in connections:
        db.add(c)

    # 2. Seed Published Posts linked to existing ContentItems
    content_items = list((await db.scalars(select(ContentItem).limit(3))).all())
    fb_conn = connections[0]
    tt_conn = connections[2]

    if content_items:
        c1 = content_items[0]
        post1_id = str(uuid.uuid4())
        post1 = PublishedPost(
            id=post1_id,
            content_id=c1.id,
            connection_id=fb_conn.id,
            channel=fb_conn.platform,
            external_post_id="fb_post_demo_88291",
            external_post_url="https://facebook.com/mochealthy/posts/fb_post_demo_88291",
            publish_status=PublishStatus.PUBLISHED.value,
            published_at=now - timedelta(days=2),
            scheduled_at=now - timedelta(days=2),
            payload_snapshot={"title": c1.title, "body": c1.body, "cta": c1.cta},
            created_at=now - timedelta(days=2),
        )
        db.add(post1)

        # Metrics for post 1
        db.add(
            PostMetric(
                id=str(uuid.uuid4()),
                published_post_id=post1_id,
                recorded_at=now - timedelta(hours=12),
                impressions=850,
                reach=620,
                likes=74,
                comments=16,
                shares=9,
                clicks=85,
                conversions=8,
                raw_data_json={"engagement_rate": 0.12},
                created_at=now - timedelta(hours=12),
            )
        )

        if len(content_items) > 1:
            c2 = content_items[1]
            post2_id = str(uuid.uuid4())
            post2 = PublishedPost(
                id=post2_id,
                content_id=c2.id,
                connection_id=tt_conn.id,
                channel=tt_conn.platform,
                external_post_id="tt_video_demo_99182",
                external_post_url="https://tiktok.com/@moc_healthy_food/video/tt_video_demo_99182",
                publish_status=PublishStatus.PUBLISHED.value,
                published_at=now - timedelta(days=1),
                scheduled_at=now - timedelta(days=1),
                payload_snapshot={"title": c2.title, "body": c2.body, "cta": c2.cta},
                created_at=now - timedelta(days=1),
            )
            db.add(post2)

            db.add(
                PostMetric(
                    id=str(uuid.uuid4()),
                    published_post_id=post2_id,
                    recorded_at=now - timedelta(hours=4),
                    impressions=3200,
                    reach=1800,
                    likes=280,
                    comments=45,
                    shares=82,
                    clicks=190,
                    conversions=24,
                    raw_data_json={"engagement_rate": 0.18},
                    created_at=now - timedelta(hours=4),
                )
            )

        if len(content_items) > 2:
            c3 = content_items[2]
            post3 = PublishedPost(
                id=str(uuid.uuid4()),
                content_id=c3.id,
                connection_id=fb_conn.id,
                channel=fb_conn.platform,
                publish_status=PublishStatus.FAILED.value,
                retry_count=1,
                max_retries=3,
                next_retry_at=now + timedelta(minutes=10),
                error_message="Simulated Meta Graph API 500 error / Temporary network timeout",
                error_code="NETWORK_TIMEOUT",
                payload_snapshot={"title": c3.title, "body": c3.body, "cta": c3.cta},
                created_at=now - timedelta(minutes=25),
            )
            db.add(post3)

    await db.commit()
    logger.info("Demo social connections (%d) seeded successfully.", len(connections))


async def seed_demo_ai_templates(db: AsyncSession) -> None:
    """Nạp các prompt templates F&B Mộc Healthy và generation logs mẫu."""
    existing_count = await db.scalar(select(func.count(PromptTemplate.id)))
    if existing_count and existing_count > 0:
        logger.info("Prompt templates already seeded (%d templates), skipping.", existing_count)
        return

    now = datetime.now(timezone.utc)

    templates = [
        PromptTemplate(
            id=str(uuid.uuid4()),
            slug="fb-copywriting-aida",
            name="Viết bài Facebook Fanpage chuẩn mô hình AIDA",
            category=PromptCategory.COPYWRITING.value,
            version=1,
            system_prompt=(
                "Bạn là chuyên gia Content Creator F&B hàng đầu cho thương hiệu Mộc Healthy. "
                "Hãy viết bằng giọng văn chân thực, tươi mới, không phóng đại nhưng lôi cuốn, "
                "tập trung vào giá trị sức khỏe của món ăn và tính tiện lợi."
            ),
            user_prompt_template=(
                "Hãy viết bài Facebook quảng bá cho món {product_name} với giá ưu đãi {price}. "
                "Điểm nhấn nguyên liệu: {ingredients}. Tone giọng: {tone}. "
                "Hãy áp dụng cấu trúc AIDA (Attention - Interest - Desire - Action) "
                "kèm 3-5 hashtags thịnh hành và lời kêu gọi hành động (CTA)."
            ),
            input_variables=["product_name", "price", "ingredients", "tone"],
            expected_output_schema=None,
            is_active=True,
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=5),
        ),
        PromptTemplate(
            id=str(uuid.uuid4()),
            slug="tiktok-short-video-script",
            name="Kịch bản video ngắn TikTok & Reels 45s",
            category=PromptCategory.CONTENT_STUDIO.value,
            version=1,
            system_prompt=(
                "Bạn là biên kịch video ngắn TikTok chuyên về ẩm thực Eat Clean. "
                "Mỗi giây đều phải giữ chân người xem bằng hình ảnh, âm thanh kích thích vị giác và insight chân thực."
            ),
            user_prompt_template=(
                "Hãy tạo kịch bản video TikTok 45 giây giới thiệu {product_name}. "
                "Đối tượng mục tiêu: {target_audience}. "
                "Cấu trúc: Hook 0-3s, Agitate 4-15s, Trải nghiệm món ăn 16-30s, Ưu đãi & CTA 31-45s."
            ),
            input_variables=["product_name", "target_audience"],
            expected_output_schema=None,
            is_active=True,
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(days=4),
        ),
        PromptTemplate(
            id=str(uuid.uuid4()),
            slug="inventory-clearance-ad",
            name="Thông điệp xả kho tồn cận date khẩn cấp",
            category=PromptCategory.PRODUCT_OPTIMIZATION.value,
            version=1,
            system_prompt=(
                "Bạn là chuyên gia xúc tiến thương mại F&B. "
                "Viết thông điệp kích cầu xả kho nhanh nhưng vẫn giữ hình ảnh cao cấp và độ tươi ngon của thương hiệu."
            ),
            user_prompt_template=(
                "Lô hàng {product_name} số lượng {quantity} còn {days_left} ngày sử dụng. "
                "Cần kích cầu gấp với mức ưu đãi {discount_percent}%. "
                "Hãy soạn thông điệp flash sale hấp dẫn để khách hàng chốt đơn trong ngày."
            ),
            input_variables=["product_name", "quantity", "days_left", "discount_percent"],
            expected_output_schema=None,
            is_active=True,
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=3),
        ),
        PromptTemplate(
            id=str(uuid.uuid4()),
            slug="customer-care-reply",
            name="Phản hồi chăm sóc khách hàng thân thiện",
            category=PromptCategory.CUSTOMER_SERVICE.value,
            version=1,
            system_prompt=(
                "Bạn là chuyên viên CSKH tận tâm của Mộc Healthy. "
                "Luôn lắng nghe, thấu hiểu, xin lỗi chân thành nếu có thiếu sót và đưa ra giải pháp làm hài lòng khách hàng."
            ),
            user_prompt_template=(
                "Khách hàng tên {customer_name} gửi phản hồi: '{feedback_content}'. "
                "Tình huống: {issue_type}. Hãy soạn tin nhắn phản hồi ấm áp, lịch sự kèm giải pháp hoặc voucher hỗ trợ."
            ),
            input_variables=["customer_name", "feedback_content", "issue_type"],
            expected_output_schema=None,
            is_active=True,
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=2),
        ),
        PromptTemplate(
            id=str(uuid.uuid4()),
            slug="marketing-campaign-ideator",
            name="Đề xuất ý tưởng chiến dịch tiếp thị xanh",
            category=PromptCategory.RECOMMENDATION.value,
            version=1,
            system_prompt=(
                "Bạn là Giám đốc Tiếp thị (CMO) của chuỗi F&B Healthy. "
                "Đề xuất chiến dịch có tính khả thi cao, chi phí hợp lý, ROI rõ ràng."
            ),
            user_prompt_template=(
                "Hãy đề xuất ý tưởng chiến dịch tiếp thị cho mùa {season_or_holiday} "
                "với ngân sách {budget} nhằm thúc đẩy doanh số nhóm món {product_category}."
            ),
            input_variables=["season_or_holiday", "budget", "product_category"],
            expected_output_schema=None,
            is_active=True,
            created_at=now - timedelta(days=1),
            updated_at=now - timedelta(days=1),
        ),
    ]

    for t in templates:
        db.add(t)

    # Seed 3 demo AIGenerationLog entries
    demo_logs = [
        AIGenerationLog(
            id=str(uuid.uuid4()),
            provider_name="MOCK",
            model_name="mock-gpt-healthy-v1",
            prompt_template_id=templates[0].id,
            prompt_slug=templates[0].slug,
            prompt_version=1,
            input_prompt_sanitized="Hãy viết bài Facebook quảng bá cho món Salad Ức Gà với giá ưu đãi 69.000đ.",
            system_prompt_sanitized=templates[0].system_prompt,
            raw_output=(
                "🥗 BỮA TRƯA HEALTHY KHÔNG CẦN CHỜ ĐỢI!\n\n"
                "Bạn đang tìm kiếm một bữa trưa vừa ngon miệng, vừa nhẹ bụng lại hỗ trợ giữ dáng? "
                "Salad Ức Gà Áp Chảo Mộc Healthy chính là lựa chọn hoàn hảo hôm nay!\n\n"
                "✨ Ức gà áp chảo vàng ươm, mềm mọng không hề khô xơ.\n"
                "✨ Rau xà lách thủy canh giòn ngọt kết hợp sốt mè rang béo bùi chuẩn vị.\n"
                "✨ Chỉ 320 kcal – đủ năng lượng cho buổi chiều làm việc hiệu quả!\n\n"
                "👉 Đặt hàng ngay hôm nay qua link bên dưới để nhận ưu đãi giảm 15%!\n"
                "#MocHealthy #SaladUcGa #EatClean #HealthyLunch"
            ),
            status=AILogStatus.SUCCESS.value,
            prompt_tokens=45,
            completion_tokens=180,
            total_tokens=225,
            estimated_cost_usd=0.000115,
            latency_ms=65,
            retry_count=0,
            created_at=now - timedelta(hours=3),
        ),
        AIGenerationLog(
            id=str(uuid.uuid4()),
            provider_name="MOCK",
            model_name="mock-gpt-healthy-v1",
            prompt_template_id=templates[1].id,
            prompt_slug=templates[1].slug,
            prompt_version=1,
            input_prompt_sanitized="Tạo kịch bản TikTok 45s cho Nước Ép Cần Tây Cam Dứa.",
            system_prompt_sanitized=templates[1].system_prompt,
            raw_output=(
                "0-3s: Cận cảnh giọt nước ép xanh mướt rơi chậm vào ly đá.\n"
                "4-15s: Uống thử và cảm nhận vị thanh mát, hoàn toàn không bị nồng đắng.\n"
                "16-30s: Liệt kê công dụng thanh lọc gan, làm sáng da.\n"
                "31-45s: Kêu gọi chốt combo 3 chai freeship."
            ),
            status=AILogStatus.SUCCESS.value,
            prompt_tokens=38,
            completion_tokens=120,
            total_tokens=158,
            estimated_cost_usd=0.000078,
            latency_ms=52,
            retry_count=0,
            created_at=now - timedelta(hours=1, minutes=20),
        ),
        AIGenerationLog(
            id=str(uuid.uuid4()),
            provider_name="MOCK",
            model_name="mock-gpt-healthy-v1",
            prompt_template_id=templates[2].id,
            prompt_slug=templates[2].slug,
            prompt_version=1,
            input_prompt_sanitized="Xả kho Sữa Hạt Hạnh Nhân Date 3 ngày.",
            system_prompt_sanitized=templates[2].system_prompt,
            raw_output="Flash sale 30% trong 24h để xả tồn cận date.",
            status=AILogStatus.SUCCESS.value,
            prompt_tokens=30,
            completion_tokens=40,
            total_tokens=70,
            estimated_cost_usd=0.000028,
            latency_ms=45,
            retry_count=0,
            created_at=now - timedelta(minutes=15),
        ),
    ]

    for log in demo_logs:
        db.add(log)

    await db.commit()
    logger.info("Demo prompt templates (%d) and AI logs (%d) seeded successfully.", len(templates), len(demo_logs))








