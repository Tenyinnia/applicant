from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import enum
import os
from uuid import UUID
from decimal import Decimal


class ApiKeyTypeEnum(str, Enum):
    LLM = "llm_key"
    VDB = "vdb_key"


class ConditionTypeEnum(enum.Enum):
    pay_as_you_go = "pay_as_you_go"
    fixed_quota = "fixed_quota"
    unlimited = "unlimited"

class ApiKeyConditions(BaseModel):
    type: ConditionTypeEnum = ConditionTypeEnum.pay_as_you_go
    rate_limit_per_min: int = Field(default=15, ge=1, le=1000)
    daily_spending_limit: Optional[Decimal] = Field(None, ge=0)
    monthly_spending_limit: Optional[Decimal] = Field(None, ge=0)

 
class ApiKeyResponse(BaseModel):
    id: UUID
    key_type: ApiKeyTypeEnum
    key_prefix: str
    name: Optional[str]
    condition_type: ConditionTypeEnum
    usage_count: int
    rate_limit_per_min: Optional[int]
    input_token_request: Optional[int]
    output_token_request: Optional[int]
    token_cost: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    rate_limit_remaining: Optional[int]

class ApiKeyValidateResponse(BaseModel):
    valid: bool
    user_id: str
    key_id: str
    conditions: ApiKeyConditions
    remaining_quota: Optional[int]

class PaginationMeta(BaseModel):
    total: int
    skip: int
    limit: int

class PaginatedResponse(BaseModel):
    data: List[ApiKeyResponse]
    pagination: PaginationMeta

class StatsResponse(BaseModel):
    key_id: str
    name: str
    total_usage: int
    remaining_quota: Optional[int]
    last_used: Optional[datetime]
    created_at: datetime
    is_active: bool
    conditions: ApiKeyConditions

class ApiKeyCreate(BaseModel):
    key_type: ApiKeyTypeEnum
    name: str = Field(..., min_length=1, max_length=255)
    conditions: ApiKeyConditions = ApiKeyConditions()
   

class ApiKeyCreateResponse(ApiKeyResponse):
    api_key: str  # Only returned once during creation

class ApiKeyUsageRequest(BaseModel):
    api_key: str
    endpoint: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    response_time_ms: Optional[int] = Field(None, ge=0)
    metadata: Dict[str, Any] = Field(default={})

class ApiKeyUsageResponse(BaseModel):
    success: bool
    cost: Decimal
    remaining_balance: Decimal
    usage_count: int
    rate_limit_remaining: int

class UsageAnalytics(BaseModel):
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: Decimal
    average_response_time: Optional[float]
    daily_usage: List[Dict[str, Any]]
    top_endpoints: List[Dict[str, Any]]


class ApiKeySummary(BaseModel):
    id: str
    key_prefix: str
    key_type: str
    description: Optional[str]
    usage_count: int
    is_active: bool
    created_at: datetime



class UsageSummary(BaseModel):
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: Decimal

class UsageStatsResponse(BaseModel):
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost: Decimal
    average_response_time: Optional[float]
    daily_usage: List[Dict[str, Any]]
    top_endpoints: List[Dict[str, Any]]


