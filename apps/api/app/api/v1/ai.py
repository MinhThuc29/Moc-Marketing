from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User
from app.api.deps import get_current_user, require_permissions
from app.schemas.ai import (
    AIProviderHealthResponse,
    AIProviderInfo,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse,
    AITestGenerateRequest,
    AITestGenerateResponse,
    AIGenerationLogResponse,
    AIGenerationLogListResponse,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["AI Provider Abstraction"])


@router.get(
    "/health",
    response_model=AIProviderHealthResponse,
    summary="Kiểm tra trạng thái sẵn sàng của AI Provider",
)
async def get_ai_health(
    provider: Optional[str] = Query(None, description="Tên provider muốn kiểm tra (MOCK, GEMINI, OPENAI)"),
    current_user: User = Depends(get_current_user),
):
    """
    Admin health indicator kiểm tra sức khỏe của AI Provider đang kích hoạt,
    đo lường độ trễ mạng (latency) và trả về thông tin model.
    """
    res = await AIService.get_health(provider)
    return AIProviderHealthResponse(
        status="ONLINE" if res.is_healthy else "OFFLINE",
        provider=res.provider_name,
        model=res.model_name,
        latency_ms=res.latency_ms,
        is_mock=res.is_mock,
        message=res.message,
    )


@router.get(
    "/providers",
    response_model=List[AIProviderInfo],
    summary="Danh sách các nhà cung cấp AI được hỗ trợ",
)
async def list_ai_providers(
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách các AI Provider được hỗ trợ và provider đang hoạt động"""
    items = AIService.list_providers()
    return [AIProviderInfo(**it) for it in items]


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------


@router.get(
    "/templates",
    response_model=PromptTemplateListResponse,
    summary="Danh sách Prompt Templates",
)
async def list_prompt_templates(
    category: Optional[str] = Query(None, description="Lọc theo nhóm nghiệp vụ"),
    is_active: Optional[bool] = Query(None, description="Lọc trạng thái kích hoạt"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    templates = await AIService.list_templates(db, category=category, is_active=is_active)
    return PromptTemplateListResponse(
        total=len(templates),
        items=[PromptTemplateResponse.model_validate(t) for t in templates],
    )


@router.get(
    "/templates/{slug}",
    response_model=PromptTemplateResponse,
    summary="Chi tiết Prompt Template theo slug",
)
async def get_prompt_template(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    template = await AIService.get_template_by_slug(db, slug)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy template slug '{slug}'.",
        )
    return PromptTemplateResponse.model_validate(template)


@router.post(
    "/templates",
    response_model=PromptTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo Prompt Template mới",
)
async def create_prompt_template(
    body: PromptTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["content.create", "settings.manage"])),
):
    template = await AIService.create_template(db, body)
    return PromptTemplateResponse.model_validate(template)


@router.put(
    "/templates/{template_id}",
    response_model=PromptTemplateResponse,
    summary="Cập nhật Prompt Template",
)
async def update_prompt_template(
    template_id: str,
    body: PromptTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["content.create", "settings.manage"])),
):
    template = await AIService.update_template(db, template_id, body)
    return PromptTemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# Test Generate Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/test-generate",
    response_model=AITestGenerateResponse,
    summary="Thử nghiệm sinh nội dung AI với Masking PII & Token Tracking",
)
async def test_generate_ai(
    body: AITestGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(["content.create", "settings.manage"])),
):
    """
    Endpoint thử nghiệm an toàn trong Sandbox:
    - Lọc bỏ tự động số điện thoại, email trước khi gửi tới provider.
    - Hỗ trợ render Prompt Template nếu cung cấp template_slug.
    - Validate cấu trúc JSON nếu expect_json=True.
    - Ghi nhận đầy đủ token và chi phí USD vào cơ sở dữ liệu.
    """
    res = await AIService.generate(
        db=db,
        prompt=body.prompt,
        system_prompt=body.system_prompt,
        template_slug=body.template_slug,
        variables=body.variables,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        expect_json=body.expect_json,
        user_id=current_user.id,
        simulate_behavior=body.simulate_behavior,
    )
    return res


# ---------------------------------------------------------------------------
# Generation Logs
# ---------------------------------------------------------------------------


@router.get(
    "/logs",
    response_model=AIGenerationLogListResponse,
    summary="Xem lịch sử các lượt gọi AI Generation",
)
async def list_ai_logs(
    provider: Optional[str] = Query(None, description="Lọc theo provider"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs, total = await AIService.list_logs(
        db,
        provider=provider,
        status_filter=status,
        limit=limit,
        offset=offset,
    )
    return AIGenerationLogListResponse(
        total=total,
        items=[AIGenerationLogResponse.model_validate(l) for l in logs],
    )


@router.get(
    "/logs/{log_id}",
    response_model=AIGenerationLogResponse,
    summary="Chi tiết một lượt gọi AI Generation",
)
async def get_ai_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log_entry = await AIService.get_log_by_id(db, log_id)
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy nhật ký AI generation log.",
        )
    return AIGenerationLogResponse.model_validate(log_entry)
