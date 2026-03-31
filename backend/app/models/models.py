from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid

class Session(Base):
    """
    会话模型
    存储用户的咨询会话信息
    """
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # VMV信息
    vision = Column(Text, nullable=True)
    mission = Column(Text, nullable=True)
    values = Column(JSON, nullable=True)
    
    # 企业基本信息
    company_name = Column(String(200), nullable=True)
    industry = Column(String(100), nullable=True)
    stage = Column(String(20), nullable=True)
    team_size = Column(String(20), nullable=True)
    selected_track = Column(Text, nullable=True)
    additional_info = Column(Text, nullable=True)
    
    # 会话状态
    current_stage = Column(Integer, default=1)
    status = Column(String(20), default="active")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """
    消息模型
    存储对话消息
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    role = Column(String(20))
    content = Column(Text)
    stage = Column(Integer)
    extra_data = Column(JSON, nullable=True)
    file_content = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="messages")


class Report(Base):
    """
    报告模型
    存储生成的分析报告
    """
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    report_type = Column(String(50))
    title = Column(String(200))
    content = Column(Text)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="reports")