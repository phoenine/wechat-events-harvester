from .base import Base, Column, Integer, String, DateTime, JSON, Text
from datetime import datetime


class MessageTask(Base):
    from_attributes = True
    __tablename__ = "message_tasks_logs"

    id = Column(String(255), primary_key=True, index=True)
    task_id = Column(String(255), nullable=False)
    # 公众号ID
    mps_id = Column(String(255), nullable=False)
    update_count = Column(Integer, default=0)
    log = Column(Text, nullable=True)
    status = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
