from core.integrations.wx.base import WxGather
from core.integrations.wx.modes.api import MpsApi
from core.integrations.wx.modes.app import MpsAppMsg
from core.integrations.wx.modes.web import MpsWeb
from core.common.config import cfg
from core.common.log import logger

__all__ = [
    "WxGather",
    "MpsApi",
    "MpsAppMsg",
    "MpsWeb",
    "search_Biz",
    "create_gather",
]


def search_Biz(kw: str = "", limit: int = 10, offset: int = 0):
    """便捷入口：保持旧调用方式不变。"""
    return WxGather().search_Biz(kw, limit=limit, offset=offset)


def create_gather(mode: str | None = None, is_add: bool = False):
    """根据配置或显式 mode 创建采集器实例。"""
    selected_mode = str(mode or cfg.get("gather.model", "app")).strip().lower()
    if selected_mode == "api":
        return MpsApi(is_add=is_add)
    if selected_mode == "web":
        return MpsWeb(is_add=is_add)
    if selected_mode == "app":
        return MpsAppMsg(is_add=is_add)

    logger.warning(f"未知采集模式: {selected_mode}, 回退到 app")
    return MpsAppMsg(is_add=is_add)

if __name__ == "__main__":
    pass
