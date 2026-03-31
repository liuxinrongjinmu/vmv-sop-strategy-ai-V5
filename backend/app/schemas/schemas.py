from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SessionCreate(BaseModel):
    """创建会话请求"""
    vision: str = Field(..., description="企业愿景")
    mission: str = Field(..., description="企业使命")
    values: List[str] = Field(..., description="企业价值观列表")
    company_name: str = Field(..., description="企业名称")
    industry: str = Field(..., description="所属行业")
    stage: str = Field(..., description="企业阶段: 0-1, 1-10, 10-N")
    team_size: Optional[str] = Field(None, description="团队规模")
    selected_track: str = Field(..., description="选定赛道")
    additional_info: Optional[str] = Field(None, description="补充信息")

class SessionUpdate(BaseModel):
    """更新会话请求"""
    vision: Optional[str] = None
    mission: Optional[str] = None
    values: Optional[List[str]] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    stage: Optional[str] = None
    team_size: Optional[str] = None
    selected_track: Optional[str] = None
    additional_info: Optional[str] = None
    current_stage: Optional[int] = None

class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    current_stage: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SessionDetail(SessionResponse):
    """会话详情"""
    vision: Optional[str] = None
    mission: Optional[str] = None
    values: Optional[List[str]] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    stage: Optional[str] = None
    team_size: Optional[str] = None
    selected_track: Optional[str] = None
    additional_info: Optional[str] = None

class MessageCreate(BaseModel):
    """创建消息请求"""
    session_id: str
    content: str = Field(..., description="消息内容")
    file_url: Optional[str] = Field(None, description="文件URL")

class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    role: str
    content: str
    stage: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReportCreate(BaseModel):
    """创建报告请求"""
    session_id: str
    report_type: str = Field(default="ten_year", description="报告类型")
    prediction: str = Field(..., description="用户预判内容")

class ReportResponse(BaseModel):
    """报告响应"""
    id: int
    title: str
    content: str
    sources: Optional[List[dict]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    filename: str
    content: str
    message: str