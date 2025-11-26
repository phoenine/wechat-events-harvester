from pydantic import BaseModel
from typing import Optional, Any


class BaseResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[Any] = None


def success_response(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}


def error_response(code: int, message: str, data=None):
    return {"code": code, "message": message, "data": data}


def format_search_kw(keyword: str):
    """
    格式化搜索关键词为单词列表
    返回关键词列表, 用于在Supabase查询中进行OR搜索
    """
    words = keyword.replace("-", " ").replace("|", " ").split(" ")
    # 过滤空字符串
    words = [word.strip() for word in words if word.strip()]
    return words
