from .base import Base, Column, Integer, String, DateTime, JSON, Text
from datetime import datetime


class MessageTask(Base):
    from_attributes = True
    __tablename__ = "message_tasks"

    id = Column(String(255), primary_key=True, index=True)
    message_type = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)

    # 定义消息模板字段，不允许为空
    message_template = Column(Text, nullable=False)
    # 定义发送接口
    web_hook_url = Column(String(500), nullable=False)
    # 定义需要通知的微信公众号ID集合
    mps_id = Column(Text, nullable=False)
    # 定义 cron_exp 表达式
    cron_exp = Column(String(100), nullable="* * 1 * *")
    # 定义任务状态字段，默认值为 pending
    status = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
