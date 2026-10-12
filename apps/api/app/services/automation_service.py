import logging
from typing import Any
from datetime import datetime, timezone
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.automation import (
    AutomationWorkflow,
    AutomationRun,
    TriggerType,
    WorkflowStatus,
    RunStatus,
    ActionType,
)
from app.models.customer import Customer
from app.schemas.automation import (
    WorkflowCreateInput,
    WorkflowUpdateInput,
    WorkflowListItem,
    WorkflowDetailResponse,
    WorkflowListResponse,
    AutomationOverviewStats,
    AutomationRunListItem,
    AutomationRunDetailResponse,
    AutomationRunListResponse,
    TriggerDispatchResult,
    TestRunResult,
)

logger = logging.getLogger("moc-healthy.automation")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AutomationService:
    @staticmethod
    def evaluate_condition(cond: dict[str, Any], context: dict[str, Any]) -> tuple[bool, str]:
        """
        Evaluates a single condition against the context dictionary.
        Supported operators: eq, neq, gt, gte, lt, lte, in, contains, is_true, is_false.
        """
        field = cond.get("field", "")
        op = cond.get("operator", "eq").lower()
        target_val = cond.get("value")

        actual_val = context.get(field)
        if actual_val is None and "." in field:
            # support nested keys, e.g. customer.segment
            parts = field.split(".")
            curr = context
            for p in parts:
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    curr = None
                    break
            actual_val = curr

        try:
            if op == "eq":
                passed = actual_val == target_val
            elif op == "neq":
                passed = actual_val != target_val
            elif op == "gt":
                passed = float(actual_val or 0) > float(target_val or 0)
            elif op == "gte":
                passed = float(actual_val or 0) >= float(target_val or 0)
            elif op == "lt":
                passed = float(actual_val or 0) < float(target_val or 0)
            elif op == "lte":
                passed = float(actual_val or 0) <= float(target_val or 0)
            elif op == "in":
                if isinstance(target_val, list):
                    passed = actual_val in target_val
                elif isinstance(actual_val, list):
                    passed = target_val in actual_val
                else:
                    passed = str(actual_val) in str(target_val)
            elif op == "contains":
                passed = str(target_val).lower() in str(actual_val or "").lower()
            elif op == "is_true":
                passed = bool(actual_val) is True
            elif op == "is_false":
                passed = bool(actual_val) is False
            else:
                passed = actual_val == target_val

            reason = f"Field '{field}' ({actual_val}) {op} {target_val} => {'PASS' if passed else 'FAIL'}"
            return passed, reason
        except Exception as e:
            logger.warning("Condition evaluation error: %s", e)
            return False, f"Error evaluating '{field}': {str(e)}"

    @staticmethod
    async def execute_action(
        db: AsyncSession,
        action: dict[str, Any],
        context: dict[str, Any],
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Executes a single workflow action.
        """
        act_type = action.get("type", "")
        phone = context.get("customer_phone") or context.get("phone", "0900000000")
        name = context.get("customer_name") or context.get("full_name", "Khách hàng")
        customer_id = context.get("customer_id") or context.get("id")

        if act_type == ActionType.SEND_ZALO_MOCK.value:
            template = action.get("template", "general_notification")
            raw_msg = action.get("message") or "Mộc Healthy gửi tặng bạn thông điệp chăm sóc sức khỏe dinh dưỡng!"
            msg = raw_msg.replace("{customer_name}", name).replace("{phone}", phone)
            return {
                "action": act_type,
                "status": "DELIVERED",
                "channel": "ZALO_OA",
                "template": template,
                "recipient": phone,
                "customer_name": name,
                "message_preview": msg[:150] + ("..." if len(msg) > 150 else ""),
                "delivered_at": utcnow().isoformat(),
            }

        elif act_type == ActionType.SEND_EMAIL_MOCK.value:
            email = context.get("customer_email") or context.get("email", "customer@example.com")
            subject = action.get("message") or "Thông báo từ Mộc Healthy"
            return {
                "action": act_type,
                "status": "SENT",
                "channel": "EMAIL",
                "recipient": email,
                "subject": subject,
                "sent_at": utcnow().isoformat(),
            }

        elif act_type == ActionType.ISSUE_PROMOTION.value:
            promo_code = action.get("promotion_code", "WELCOME20")
            return {
                "action": act_type,
                "status": "ISSUED",
                "promotion_code": promo_code,
                "recipient": phone,
                "valid_days": 14,
                "issued_at": utcnow().isoformat(),
            }

        elif act_type == ActionType.ADD_LOYALTY_POINTS.value:
            pts = int(action.get("points", 10))
            if not dry_run and customer_id:
                try:
                    res_c = await db.execute(select(Customer).where(Customer.id == str(customer_id)))
                    cust = res_c.scalar_one_or_none()
                    if cust:
                        cust.loyalty_points = (cust.loyalty_points or 0) + pts
                        await db.flush()
                except Exception as e:
                    logger.warning("Could not persist loyalty points in automation: %s", e)

            return {
                "action": act_type,
                "status": "AWARDED",
                "points_awarded": pts,
                "customer_id": customer_id,
                "awarded_at": utcnow().isoformat(),
            }

        elif act_type == ActionType.ADD_CUSTOMER_TAG.value:
            tag = action.get("tag", "automation_engaged")
            if not dry_run and customer_id:
                try:
                    res_c = await db.execute(select(Customer).where(Customer.id == str(customer_id)))
                    cust = res_c.scalar_one_or_none()
                    if cust:
                        existing_tags = cust.tags if isinstance(cust.tags, list) else []
                        if tag not in existing_tags:
                            cust.tags = existing_tags + [tag]
                            await db.flush()
                except Exception as e:
                    logger.warning("Could not persist tag in automation: %s", e)

            return {
                "action": act_type,
                "status": "TAGGED",
                "tag": tag,
                "customer_id": customer_id,
                "tagged_at": utcnow().isoformat(),
            }

        elif act_type == ActionType.CREATE_NOTIFICATION.value:
            title = action.get("notification_title") or f"Thông báo tự động: {name}"
            body = action.get("notification_body") or action.get("message") or "Hệ thống tự động kích hoạt tiến trình."
            return {
                "action": act_type,
                "status": "NOTIFIED",
                "title": title,
                "body": body,
                "severity": "INFO",
                "notified_at": utcnow().isoformat(),
            }

        elif act_type == ActionType.CREATE_RECOMMENDATION.value:
            title = action.get("notification_title") or "Đề xuất chiến dịch tự động từ AI Marketing"
            return {
                "action": act_type,
                "status": "RECOMMENDATION_CREATED",
                "recommendation_title": title,
                "requires_human_approval": True,
                "created_at": utcnow().isoformat(),
            }

        elif act_type == ActionType.CREATE_CAMPAIGN_DRAFT.value:
            code = f"CAMP-AUTO-{utcnow().strftime('%m%d%H%M')}"
            return {
                "action": act_type,
                "status": "CAMPAIGN_DRAFT_CREATED",
                "campaign_code": code,
                "status_state": "DRAFT",
                "created_at": utcnow().isoformat(),
            }

        elif act_type == ActionType.WAIT_HOURS.value:
            wait_h = int(action.get("wait_hours", 2))
            return {
                "action": act_type,
                "status": "SCHEDULED",
                "wait_hours": wait_h,
                "scheduled_resume": utcnow().isoformat(),
            }

        else:
            return {
                "action": act_type,
                "status": "EXECUTED",
                "details": action,
                "executed_at": utcnow().isoformat(),
            }

    @staticmethod
    async def get_overview_stats(db: AsyncSession) -> AutomationOverviewStats:
        """
        Aggregates summary statistics for the automation hub.
        """
        res_wf = await db.execute(select(AutomationWorkflow))
        workflows = res_wf.scalars().all()

        total_wf = len(workflows)
        active_wf = sum(1 for w in workflows if w.status == WorkflowStatus.ACTIVE.value)
        paused_wf = sum(1 for w in workflows if w.status == WorkflowStatus.PAUSED.value)
        active_templates = sum(1 for w in workflows if w.is_system_template and w.status == WorkflowStatus.ACTIVE.value)

        total_runs = sum(w.total_runs for w in workflows)
        successful_runs = sum(w.successful_runs for w in workflows)
        failed_runs = sum(w.failed_runs for w in workflows)

        success_rate = (successful_runs / total_runs * 100.0) if total_runs > 0 else 100.0

        return AutomationOverviewStats(
            total_workflows=total_wf,
            active_workflows=active_wf,
            paused_workflows=paused_wf,
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            success_rate=round(success_rate, 1),
            active_templates_count=active_templates,
        )

    @staticmethod
    async def list_workflows(
        db: AsyncSession,
        trigger_type: str | None = None,
        status_filter: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> WorkflowListResponse:
        """
        Queries workflows with filters, search, and pagination.
        """
        query = select(AutomationWorkflow)

        if trigger_type and trigger_type != "ALL":
            query = query.where(AutomationWorkflow.trigger_type == trigger_type)
        if status_filter and status_filter != "ALL":
            query = query.where(AutomationWorkflow.status == status_filter)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    AutomationWorkflow.name.ilike(term),
                    AutomationWorkflow.code.ilike(term),
                    AutomationWorkflow.description.ilike(term),
                )
            )

        # Count total
        count_q = select(func.count()).select_from(query.subquery())
        res_count = await db.execute(count_q)
        total = res_count.scalar_one()

        # Paginate
        offset = (page - 1) * limit
        query = query.order_by(
            desc(AutomationWorkflow.is_system_template),
            desc(AutomationWorkflow.created_at)
        ).offset(offset).limit(limit)

        res_items = await db.execute(query)
        workflows = res_items.scalars().all()

        items = []
        for w in workflows:
            sr = (w.successful_runs / w.total_runs * 100.0) if w.total_runs > 0 else 100.0
            items.append(
                WorkflowListItem(
                    id=w.id,
                    name=w.name,
                    code=w.code,
                    description=w.description,
                    trigger_type=w.trigger_type,
                    trigger_config=w.trigger_config or {},
                    conditions=w.conditions or [],
                    actions=w.actions or [],
                    status=w.status,
                    is_system_template=w.is_system_template,
                    total_runs=w.total_runs,
                    successful_runs=w.successful_runs,
                    failed_runs=w.failed_runs,
                    success_rate=round(sr, 1),
                    created_at=w.created_at,
                    updated_at=w.updated_at,
                )
            )

        return WorkflowListResponse(items=items, total=total)

    @staticmethod
    async def get_workflow_detail(db: AsyncSession, workflow_id: str) -> WorkflowDetailResponse:
        """
        Fetches detailed workflow definition with recent execution runs.
        """
        res = await db.execute(select(AutomationWorkflow).where(AutomationWorkflow.id == workflow_id))
        w = res.scalar_one_or_none()
        if not w:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kịch bản tự động hóa")

        # Fetch recent 5 runs
        res_runs = await db.execute(
            select(AutomationRun)
            .where(AutomationRun.workflow_id == workflow_id)
            .order_by(desc(AutomationRun.created_at))
            .limit(10)
        )
        runs = res_runs.scalars().all()

        recent_runs = [
            AutomationRunListItem(
                id=r.id,
                workflow_id=r.workflow_id,
                workflow_name=w.name,
                workflow_code=w.code,
                trigger_type=r.trigger_type,
                trigger_source_id=r.trigger_source_id,
                status=r.status,
                started_at=r.started_at,
                completed_at=r.completed_at,
                step_count=len(r.step_runs) if isinstance(r.step_runs, list) else 0,
                error_message=r.error_message,
                created_at=r.created_at,
            )
            for r in runs
        ]

        sr = (w.successful_runs / w.total_runs * 100.0) if w.total_runs > 0 else 100.0
        return WorkflowDetailResponse(
            id=w.id,
            name=w.name,
            code=w.code,
            description=w.description,
            trigger_type=w.trigger_type,
            trigger_config=w.trigger_config or {},
            conditions=w.conditions or [],
            actions=w.actions or [],
            status=w.status,
            is_system_template=w.is_system_template,
            total_runs=w.total_runs,
            successful_runs=w.successful_runs,
            failed_runs=w.failed_runs,
            success_rate=round(sr, 1),
            created_at=w.created_at,
            updated_at=w.updated_at,
            recent_runs=recent_runs,
        )

    @staticmethod
    async def create_workflow(
        db: AsyncSession,
        payload: WorkflowCreateInput,
        user_id: str | None = None,
    ) -> WorkflowListItem:
        """
        Creates a new marketing automation workflow.
        """
        # Validate unique code
        res_dup = await db.execute(select(AutomationWorkflow).where(AutomationWorkflow.code == payload.code.strip()))
        if res_dup.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mã kịch bản '{payload.code}' đã tồn tại trong hệ thống.",
            )

        wf = AutomationWorkflow(
            name=payload.name.strip(),
            code=payload.code.strip().upper(),
            description=payload.description.strip() if payload.description else None,
            trigger_type=payload.trigger_type,
            trigger_config=payload.trigger_config,
            conditions=[c.model_dump() for c in payload.conditions],
            actions=[a.model_dump() for a in payload.actions],
            status=payload.status,
            is_system_template=payload.is_system_template,
            total_runs=0,
            successful_runs=0,
            failed_runs=0,
            created_by_user_id=user_id,
        )
        db.add(wf)
        await db.commit()
        await db.refresh(wf)

        return WorkflowListItem(
            id=wf.id,
            name=wf.name,
            code=wf.code,
            description=wf.description,
            trigger_type=wf.trigger_type,
            trigger_config=wf.trigger_config or {},
            conditions=wf.conditions or [],
            actions=wf.actions or [],
            status=wf.status,
            is_system_template=wf.is_system_template,
            total_runs=0,
            successful_runs=0,
            failed_runs=0,
            success_rate=100.0,
            created_at=wf.created_at,
            updated_at=wf.updated_at,
        )

    @staticmethod
    async def update_workflow(
        db: AsyncSession,
        workflow_id: str,
        payload: WorkflowUpdateInput,
    ) -> WorkflowListItem:
        """
        Updates an existing workflow definition.
        """
        res = await db.execute(select(AutomationWorkflow).where(AutomationWorkflow.id == workflow_id))
        wf = res.scalar_one_or_none()
        if not wf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kịch bản tự động hóa")

        if payload.name is not None:
            wf.name = payload.name.strip()
        if payload.description is not None:
            wf.description = payload.description.strip() if payload.description else None
        if payload.trigger_type is not None:
            wf.trigger_type = payload.trigger_type
        if payload.trigger_config is not None:
            wf.trigger_config = payload.trigger_config
        if payload.conditions is not None:
            wf.conditions = [c.model_dump() for c in payload.conditions]
        if payload.actions is not None:
            wf.actions = [a.model_dump() for a in payload.actions]
        if payload.status is not None:
            wf.status = payload.status

        wf.updated_at = utcnow()
        await db.commit()
        await db.refresh(wf)

        sr = (wf.successful_runs / wf.total_runs * 100.0) if wf.total_runs > 0 else 100.0
        return WorkflowListItem(
            id=wf.id,
            name=wf.name,
            code=wf.code,
            description=wf.description,
            trigger_type=wf.trigger_type,
            trigger_config=wf.trigger_config or {},
            conditions=wf.conditions or [],
            actions=wf.actions or [],
            status=wf.status,
            is_system_template=wf.is_system_template,
            total_runs=wf.total_runs,
            successful_runs=wf.successful_runs,
            failed_runs=wf.failed_runs,
            success_rate=round(sr, 1),
            created_at=wf.created_at,
            updated_at=wf.updated_at,
        )

    @staticmethod
    async def toggle_workflow_status(
        db: AsyncSession,
        workflow_id: str,
        new_status: str,
    ) -> WorkflowListItem:
        """
        Toggles or updates workflow operational status (ACTIVE, PAUSED, DRAFT, ARCHIVED).
        """
        res = await db.execute(select(AutomationWorkflow).where(AutomationWorkflow.id == workflow_id))
        wf = res.scalar_one_or_none()
        if not wf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kịch bản")

        wf.status = new_status
        wf.updated_at = utcnow()
        await db.commit()
        await db.refresh(wf)

        sr = (wf.successful_runs / wf.total_runs * 100.0) if wf.total_runs > 0 else 100.0
        return WorkflowListItem(
            id=wf.id,
            name=wf.name,
            code=wf.code,
            description=wf.description,
            trigger_type=wf.trigger_type,
            trigger_config=wf.trigger_config or {},
            conditions=wf.conditions or [],
            actions=wf.actions or [],
            status=wf.status,
            is_system_template=wf.is_system_template,
            total_runs=wf.total_runs,
            successful_runs=wf.successful_runs,
            failed_runs=wf.failed_runs,
            success_rate=round(sr, 1),
            created_at=wf.created_at,
            updated_at=wf.updated_at,
        )

    @staticmethod
    async def delete_workflow(db: AsyncSession, workflow_id: str) -> None:
        """
        Deletes a workflow. Prohibits deleting protected system templates.
        """
        res = await db.execute(select(AutomationWorkflow).where(AutomationWorkflow.id == workflow_id))
        wf = res.scalar_one_or_none()
        if not wf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kịch bản")

        if wf.is_system_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa kịch bản hệ thống mặc định (System Template). Bạn có thể Tạm dừng (PAUSE) kịch bản thay thế.",
            )

        await db.delete(wf)
        await db.commit()

    @staticmethod
    async def list_runs(
        db: AsyncSession,
        workflow_id: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> AutomationRunListResponse:
        """
        Retrieves paginated audit log runs with workflow names.
        """
        query = select(AutomationRun, AutomationWorkflow.name, AutomationWorkflow.code).join(
            AutomationWorkflow, AutomationRun.workflow_id == AutomationWorkflow.id, isouter=True
        )

        if workflow_id:
            query = query.where(AutomationRun.workflow_id == workflow_id)
        if status_filter and status_filter != "ALL":
            query = query.where(AutomationRun.status == status_filter)

        count_q = select(func.count()).select_from(query.subquery())
        res_count = await db.execute(count_q)
        total = res_count.scalar_one()

        offset = (page - 1) * limit
        query = query.order_by(desc(AutomationRun.created_at)).offset(offset).limit(limit)

        res_items = await db.execute(query)
        rows = res_items.all()

        items = []
        for r, wf_name, wf_code in rows:
            step_count = len(r.step_runs) if isinstance(r.step_runs, list) else 0
            items.append(
                AutomationRunListItem(
                    id=r.id,
                    workflow_id=r.workflow_id,
                    workflow_name=wf_name or "Kịch bản đã xóa",
                    workflow_code=wf_code or "N/A",
                    trigger_type=r.trigger_type,
                    trigger_source_id=r.trigger_source_id,
                    status=r.status,
                    started_at=r.started_at,
                    completed_at=r.completed_at,
                    step_count=step_count,
                    error_message=r.error_message,
                    created_at=r.created_at,
                )
            )

        return AutomationRunListResponse(items=items, total=total)

    @staticmethod
    async def get_run_detail(db: AsyncSession, run_id: str) -> AutomationRunDetailResponse:
        """
        Retrieves detailed step-by-step logs for a specific run.
        """
        query = select(AutomationRun, AutomationWorkflow.name, AutomationWorkflow.code).join(
            AutomationWorkflow, AutomationRun.workflow_id == AutomationWorkflow.id, isouter=True
        ).where(AutomationRun.id == run_id)

        res = await db.execute(query)
        row = res.first()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy nhật ký thực thi")

        r, wf_name, wf_code = row
        step_runs = r.step_runs if isinstance(r.step_runs, list) else []
        return AutomationRunDetailResponse(
            id=r.id,
            workflow_id=r.workflow_id,
            workflow_name=wf_name or "Kịch bản đã xóa",
            workflow_code=wf_code or "N/A",
            trigger_type=r.trigger_type,
            trigger_source_id=r.trigger_source_id,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
            step_count=len(step_runs),
            error_message=r.error_message,
            created_at=r.created_at,
            step_runs=step_runs,
            metadata_json=r.metadata_json or {},
        )

    @staticmethod
    async def dispatch_trigger(
        db: AsyncSession,
        trigger_type: str,
        source_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> TriggerDispatchResult:
        """
        Dispatches an event to all matching ACTIVE workflows.
        Evaluates conditions, executes actions sequentially, and records execution audit telemetry.
        """
        ctx = context or {}
        # 1. Query active workflows for this trigger
        res_wf = await db.execute(
            select(AutomationWorkflow)
            .where(
                AutomationWorkflow.trigger_type == trigger_type,
                AutomationWorkflow.status == WorkflowStatus.ACTIVE.value,
            )
        )
        workflows = res_wf.scalars().all()

        run_ids = []
        executed_count = 0

        for wf in workflows:
            # 2. Evaluate all conditions
            conditions_pass = True
            eval_logs = []
            conditions_list = wf.conditions if isinstance(wf.conditions, list) else []

            for cond in conditions_list:
                passed, reason = AutomationService.evaluate_condition(cond, ctx)
                eval_logs.append({"condition": cond, "passed": passed, "reason": reason})
                if not passed:
                    conditions_pass = False
                    break

            if not conditions_pass:
                logger.info("Workflow '%s' conditions not met, skipping run.", wf.code)
                continue

            # 3. Create run record
            run = AutomationRun(
                workflow_id=wf.id,
                trigger_type=trigger_type,
                trigger_source_id=source_id,
                status=RunStatus.RUNNING.value,
                started_at=utcnow(),
                step_runs=[],
                metadata_json={"context": ctx, "evaluations": eval_logs},
            )
            db.add(run)
            await db.flush()

            # 4. Execute actions
            actions_list = wf.actions if isinstance(wf.actions, list) else []
            step_runs_results = []
            has_error = False
            last_err = None

            for idx, act in enumerate(actions_list):
                try:
                    out = await AutomationService.execute_action(db, act, ctx, dry_run=False)
                    step_runs_results.append({
                        "step_index": idx + 1,
                        "action_type": act.get("type", "UNKNOWN"),
                        "status": "SUCCESS",
                        "output": out,
                        "executed_at": utcnow().isoformat(),
                    })
                except Exception as ex:
                    has_error = True
                    last_err = str(ex)
                    step_runs_results.append({
                        "step_index": idx + 1,
                        "action_type": act.get("type", "UNKNOWN"),
                        "status": "FAILED",
                        "error": last_err,
                        "executed_at": utcnow().isoformat(),
                    })
                    break

            # 5. Finalize run status
            run.completed_at = utcnow()
            run.step_runs = step_runs_results
            if has_error:
                run.status = RunStatus.FAILED.value
                run.error_message = last_err
                wf.failed_runs = (wf.failed_runs or 0) + 1
            else:
                run.status = RunStatus.SUCCESS.value
                wf.successful_runs = (wf.successful_runs or 0) + 1

            wf.total_runs = (wf.total_runs or 0) + 1
            run_ids.append(run.id)
            executed_count += 1

        await db.commit()

        summary = f"Kích hoạt trigger {trigger_type}: Đã so khớp {len(workflows)} kịch bản, thực thi thành công {executed_count} lượt chạy."
        return TriggerDispatchResult(
            trigger_type=trigger_type,
            matched_workflows_count=len(workflows),
            executed_runs_count=executed_count,
            run_ids=run_ids,
            summary=summary,
        )

    @staticmethod
    async def test_run_workflow(
        db: AsyncSession,
        workflow_id: str,
        test_context: dict[str, Any],
    ) -> TestRunResult:
        """
        Executes a dry-run test of a workflow without committing destructive changes.
        """
        res = await db.execute(select(AutomationWorkflow).where(AutomationWorkflow.id == workflow_id))
        wf = res.scalar_one_or_none()
        if not wf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kịch bản")

        # Evaluate conditions
        conditions_pass = True
        eval_logs = []
        conditions_list = wf.conditions if isinstance(wf.conditions, list) else []

        for cond in conditions_list:
            passed, reason = AutomationService.evaluate_condition(cond, test_context)
            eval_logs.append({"condition": cond, "passed": passed, "reason": reason})
            if not passed:
                conditions_pass = False

        step_runs_results = []
        error_msg = None
        status_res = "SUCCESS"

        if not conditions_pass:
            status_res = "CONDITIONS_UNMET"
        else:
            actions_list = wf.actions if isinstance(wf.actions, list) else []
            for idx, act in enumerate(actions_list):
                try:
                    out = await AutomationService.execute_action(db, act, test_context, dry_run=True)
                    step_runs_results.append({
                        "step_index": idx + 1,
                        "action_type": act.get("type", "UNKNOWN"),
                        "status": "SUCCESS (DRY_RUN)",
                        "output": out,
                        "executed_at": utcnow().isoformat(),
                    })
                except Exception as ex:
                    error_msg = str(ex)
                    status_res = "FAILED"
                    step_runs_results.append({
                        "step_index": idx + 1,
                        "action_type": act.get("type", "UNKNOWN"),
                        "status": "FAILED",
                        "error": error_msg,
                        "executed_at": utcnow().isoformat(),
                    })
                    break

        return TestRunResult(
            workflow_id=wf.id,
            workflow_name=wf.name,
            status=status_res,
            conditions_passed=conditions_pass,
            condition_evaluations=eval_logs,
            step_runs=step_runs_results,
            error_message=error_msg,
        )
