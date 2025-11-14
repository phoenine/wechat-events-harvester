from .base import Base, Column, String, Integer, DateTime, Text


class Tags(Base):
    __tablename__ = "tags"

    id = Column(String(255), primary_key=True)
    name = Column(String(255))
    # 标签封面图片URL
    cover = Column(String(255))
    intro = Column(String(255))
    # 标签状态（如：0-禁用，1-启用）
    status = Column(Integer)
    mps_id = Column(Text, nullable=False)
    sync_time = Column(Integer)
    update_time = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
