import asyncio
import json
import os
import time
from typing import Optional, Dict, Any, List, Type, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.models.ai import (
    PromptTemplate,
    AIGenerationLog,
    AILogStatus,
    PromptCategory,
)
from app.schemas.ai import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    AITestGenerateResponse,
)
from app.services.ai_providers.base import (
    BaseAIProvider,
    AITextResult,
    AIJsonResult,
    AIHealthResult,
)
from app.services.ai_providers.sanitizer import mask_pii
from app.services.ai_providers.mock_provider import MockAIProvider
from app.services.ai_providers.registry import (
    get_ai_provider,
    list_supported_providers,
)


class AIService:
    @staticmethod
    async def get_health(provider_type: Optional[str] = None) -> AIHealthResult:
        provider = get_ai_provider(provider_type)
        return await provider.health_check()

    @staticmethod
    def list_providers() -> List[Dict[str, Any]]:
        return list_supported_providers()

    # -------------------------------------------------------------
    # Prompt Template Management
    # -------------------------------------------------------------

    @staticmethod
    async def list_templates(
        db: AsyncSession,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[PromptTemplate]:
        query = select(PromptTemplate).order_by(PromptTemplate.slug)
        if category:
            query = query.where(PromptTemplate.category == category)
        if is_active is not None:
            query = query.where(PromptTemplate.is_active == is_active)

        res = await db.scalars(query)
        return list(res.all())

    @staticmethod
    async def get_template_by_slug(
        db: AsyncSession,
        slug: str,
    ) -> Optional[PromptTemplate]:
        query = select(PromptTemplate).where(PromptTemplate.slug == slug)
        return await db.scalar(query)

    @staticmethod
    async def get_template_by_id(
        db: AsyncSession,
        template_id: str,
    ) -> Optional[PromptTemplate]:
        query = select(PromptTemplate).where(PromptTemplate.id == template_id)
        return await db.scalar(query)

    @staticmethod
    async def create_template(
        db: AsyncSession,
        data: PromptTemplateCreate,
    ) -> PromptTemplate:
        existing = await AIService.get_template_by_slug(db, data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prompt template slug '{data.slug}' đã tồn tại trong hệ thống.",
            )

        template = PromptTemplate(
            slug=data.slug,
            name=data.name,
            category=data.category,
            version=1,
            system_prompt=data.system_prompt,
            user_prompt_template=data.user_prompt_template,
            input_variables=data.input_variables,
            expected_output_schema=data.expected_output_schema,
            is_active=data.is_active,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: str,
        data: PromptTemplateUpdate,
    ) -> PromptTemplate:
        template = await AIService.get_template_by_id(db, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy prompt template.",
            )

        if data.name is not None:
            template.name = data.name
        if data.category is not None:
            template.category = data.category
        if data.system_prompt is not None:
            template.system_prompt = data.system_prompt
        if data.user_prompt_template is not None:
            template.user_prompt_template = data.user_prompt_template
        if data.input_variables is not None:
            template.input_variables = data.input_variables
        if data.expected_output_schema is not None:
            template.expected_output_schema = data.expected_output_schema
        if data.is_active is not None:
            template.is_active = data.is_active

        if data.bump_version:
            template.version += 1

        template.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(template)
        return template

    # -------------------------------------------------------------
    # AI Generation Pipeline with Masking, Retry, and Audit Logging
    # -------------------------------------------------------------

    @staticmethod
    async def generate(
        db: AsyncSession,
        prompt: str,
        system_prompt: Optional[str] = None,
        template_slug: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        expect_json: bool = False,
        provider_override: Optional[BaseAIProvider] = None,
        user_id: Optional[str] = None,
        simulate_behavior: Optional[str] = None,
    ) -> AITestGenerateResponse:
        """
        Quy trình chuẩn hóa thực thi AI:
        1. Khử thông tin định danh nhạy cảm (PII Masking).
        2. Tải và render template (nếu có template_slug).
        3. Khởi tạo AI Provider theo cấu hình môi trường hoặc cờ kiểm thử.
        4. Thực thi với cơ chế Timeout và Exponential Backoff Retry.
        5. Xác thực cấu trúc dữ liệu Pydantic (nếu yêu cầu JSON).
        6. Lưu vết toàn diện vào AIGenerationLog.
        """
        start_pipeline = time.perf_counter()

        # 1. Template resolution
        tpl_id = None
        tpl_version = None
        effective_prompt = prompt
        effective_system = system_prompt

        if template_slug:
            tpl = await AIService.get_template_by_slug(db, template_slug)
            if tpl:
                tpl_id = tpl.id
                tpl_version = tpl.version
                effective_system = tpl.system_prompt or system_prompt
                user_template = tpl.user_prompt_template
                if variables:
                    for k, v in variables.items():
                        user_template = user_template.replace(f"{{{k}}}", str(v))
                effective_prompt = user_template

        # 2. PII Sanitization Guardrail
        sanitized_prompt = mask_pii(effective_prompt)
        sanitized_system = mask_pii(effective_system) if effective_system else None

        # 3. Provider Resolution
        if provider_override:
            provider = provider_override
        elif simulate_behavior:
            # Dành riêng cho test cases mô phỏng các trạng thái failure
            sim_timeout = simulate_behavior == "timeout"
            sim_malformed = simulate_behavior == "malformed_json"
            sim_fail = simulate_behavior == "fail"
            sim_retry = 1 if simulate_behavior == "retry_success" else 0
            provider = MockAIProvider(
                simulate_timeout=sim_timeout,
                simulate_malformed_json=sim_malformed,
                simulate_transient_failure=sim_retry,
                is_available=not sim_fail,
            )
        else:
            provider = get_ai_provider()

        # 4. Execution with Retry & Timeout
        timeout_sec = float(os.getenv("AI_TIMEOUT_SECONDS", "15.0"))
        max_retries = int(os.getenv("AI_MAX_RETRIES", "2"))  # Tổng tối đa 3 lần thử
        current_retry = 0

        final_status = AILogStatus.SUCCESS.value
        error_msg = None
        text_output = None
        json_output = None
        raw_output_text = None
        p_tokens = 0
        c_tokens = 0
        t_tokens = 0
        cost_usd = 0.0

        for attempt in range(max_retries + 1):
            current_retry = attempt
            try:
                if expect_json or schema:
                    # Chạy JSON Generation với timeout
                    res_json: AIJsonResult = await asyncio.wait_for(
                        provider.generate_json(
                            prompt=sanitized_prompt,
                            schema=schema,
                            system_prompt=sanitized_system,
                            max_tokens=max_tokens,
                            temperature=temperature,
                        ),
                        timeout=timeout_sec,
                    )
                    raw_output_text = res_json.raw_text
                    p_tokens = res_json.prompt_tokens
                    c_tokens = res_json.completion_tokens
                    t_tokens = res_json.total_tokens
                    cost_usd = res_json.estimated_cost_usd

                    # Validate JSON syntax
                    try:
                        parsed = json.loads(res_json.raw_text)
                    except Exception as json_err:
                        raise ValueError(f"Malformed JSON output: {str(json_err)}")

                    # Validate với Pydantic schema nếu có
                    if schema:
                        validated_model = schema.model_validate(parsed)
                        json_output = validated_model.model_dump()
                    else:
                        json_output = parsed

                    final_status = AILogStatus.SUCCESS.value
                    error_msg = None
                    break

                else:
                    # Chạy Text Generation với timeout
                    res_text: AITextResult = await asyncio.wait_for(
                        provider.generate_text(
                            prompt=sanitized_prompt,
                            system_prompt=sanitized_system,
                            max_tokens=max_tokens,
                            temperature=temperature,
                        ),
                        timeout=timeout_sec,
                    )
                    text_output = res_text.text
                    raw_output_text = res_text.text
                    p_tokens = res_text.prompt_tokens
                    c_tokens = res_text.completion_tokens
                    t_tokens = res_text.total_tokens
                    cost_usd = res_text.estimated_cost_usd

                    final_status = AILogStatus.SUCCESS.value
                    error_msg = None
                    break

            except asyncio.TimeoutError:
                final_status = AILogStatus.TIMEOUT.value
                error_msg = f"Yêu cầu AI vượt quá giới hạn thời gian ({timeout_sec}s)."
                if attempt < max_retries:
                    await asyncio.sleep(0.05 * (2 ** attempt))
                    continue

            except (ValueError, ValidationError) as val_err:
                final_status = AILogStatus.VALIDATION_ERROR.value
                error_msg = f"Dữ liệu JSON đầu ra không hợp lệ: {str(val_err)}"
                if attempt < max_retries:
                    await asyncio.sleep(0.05 * (2 ** attempt))
                    continue

            except Exception as e:
                final_status = AILogStatus.FAILED.value
                error_msg = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(0.05 * (2 ** attempt))
                    continue

        total_latency = int((time.perf_counter() - start_pipeline) * 1000)

        # 5. Lưu vết vào AIGenerationLog
        log_entry = AIGenerationLog(
            provider_name=provider.provider_name,
            model_name=provider.model_name,
            prompt_template_id=tpl_id,
            prompt_slug=template_slug,
            prompt_version=tpl_version,
            input_prompt_sanitized=sanitized_prompt,
            system_prompt_sanitized=sanitized_system,
            raw_output=raw_output_text,
            parsed_json=json_output,
            status=final_status,
            error_message=error_msg,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=t_tokens,
            estimated_cost_usd=cost_usd,
            latency_ms=total_latency,
            retry_count=current_retry,
            created_by_user_id=user_id,
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)

        return AITestGenerateResponse(
            success=(final_status == AILogStatus.SUCCESS.value),
            text_output=text_output,
            json_output=json_output,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=t_tokens,
            estimated_cost_usd=cost_usd,
            latency_ms=total_latency,
            provider=provider.provider_name,
            model=provider.model_name,
            log_id=log_entry.id,
            sanitized_input=sanitized_prompt,
            error_message=error_msg,
        )

    # -------------------------------------------------------------
    # Generation Logs Querying
    # -------------------------------------------------------------

    @staticmethod
    async def list_logs(
        db: AsyncSession,
        provider: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AIGenerationLog], int]:
        query = select(AIGenerationLog).order_by(desc(AIGenerationLog.created_at))

        if provider:
            query = query.where(AIGenerationLog.provider_name == provider.upper())
        if status_filter:
            query = query.where(AIGenerationLog.status == status_filter.upper())

        # Total count
        from sqlalchemy import func
        count_q = select(func.count(AIGenerationLog.id))
        if provider:
            count_q = count_q.where(AIGenerationLog.provider_name == provider.upper())
        if status_filter:
            count_q = count_q.where(AIGenerationLog.status == status_filter.upper())

        total = await db.scalar(count_q) or 0
        items = await db.scalars(query.offset(offset).limit(limit))

        return list(items.all()), total

    @staticmethod
    async def get_log_by_id(
        db: AsyncSession,
        log_id: str,
    ) -> Optional[AIGenerationLog]:
        query = select(AIGenerationLog).where(AIGenerationLog.id == log_id)
        return await db.scalar(query)
