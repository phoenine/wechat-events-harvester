# 从 sqlalchemy 模块导入所需的列类型和数据库相关功能
from .base import Base, Column, Integer, String, Text


class ConfigManagement(Base):
    from_attributes = True
    __tablename__ = "config_management"

    config_key = Column(
        String(100), primary_key=True, unique=True, index=True, nullable=False
    )
    config_value = Column(Text, nullable=False)
    description = Column(String(200))
