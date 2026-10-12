from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ConditionItem(BaseModel):
    field: str
    operator: str = "eq"  # eq, neq, gt, gte, lt, lte, in, contains
    value: Any = None


class ActionItem(BaseModel):
    type: str  # SEND_ZALO_MOCK, SEND_EMAIL_MOCK, ISSUE_PROMOTION, ADD_LOYALTY_POINTS, ADD_CUSTOMER_TAG, CREATE_NOTIFICATION, CREATE_RECOMMENDATION, CREATE_CAMPAIGN_DRAFT, WAIT_HOURS
    template: str | None = None
    message: str | None = None
    promotion_code: str | None = None
    points: int | None = None
    tag: str | None = None
    notification_title: str | None = None
    notification_body: str | None = None
    wait_hours: int | None = None
    params: dict[str, Any] | None = None


class WorkflowCreateInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=100)
    description: str | None = None
    trigger_type: str
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    conditions: list[ConditionItem] = Field(default_factory=list)
    actions: list[ActionItem] = Field(default_factory=list)
    status: str = "ACTIVE"
    is_system_template: bool = False


class WorkflowUpdateInput(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_type: str | None = None
    trigger_config: dict[str, Any] | None = None
    conditions: list[ConditionItem] | None = None
    actions: list[ActionItem] | None = None
    status: str | None = None


class WorkflowStatusUpdateInput(BaseModel):
    status: str = Field(..., pattern="^(ACTIVE|PAUSED|DRAFT|ARCHIVED)$")


class WorkflowListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    description: str | None = None
    trigger_type: str
    trigger_config: dict[str, Any] = Field(default_factory=dict)
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    is_system_template: bool
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    created_at: datetime
    updated_at: datetime


class AutomationRunListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_id: str
    workflow_name: str | None = None
    workflow_code: str | None = None
    trigger_type: str
    trigger_source_id: str | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    step_count: int = 0
    error_message: str | None = None
    created_at: datetime


class WorkflowDetailResponse(WorkflowListItem):
    recent_runs: list[AutomationRunListItem] = Field(default_factory=list)


class WorkflowListResponse(BaseModel):
    items: list[WorkflowListItem]
    total: int


class AutomationOverviewStats(BaseModel):
    total_workflows: int
    active_workflows: int
    paused_workflows: int
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    active_templates_count: int


class AutomationRunDetailResponse(AutomationRunListItem):
    step_runs: list[dict[str, Any]] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AutomationRunListResponse(BaseModel):
    items: list[AutomationRunListItem]
    total: int


class TriggerDispatchInput(BaseModel):
    trigger_type: str
    source_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class TriggerDispatchResult(BaseModel):
    trigger_type: str
    matched_workflows_count: int
    executed_runs_count: int
    run_ids: list[str]
    summary: str


class TestRunInput(BaseModel):
    test_context: dict[str, Any] = Field(default_factory=dict)


class TestRunResult(BaseModel):
    workflow_id: str
    workflow_name: str
    status: str
    conditions_passed: bool
    condition_evaluations: list[dict[str, Any]]
    step_runs: list[dict[str, Any]]
    error_message: str | None = None
