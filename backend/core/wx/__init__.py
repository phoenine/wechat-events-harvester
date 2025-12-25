from core.wx.model import *
from core.wx.base import WxGather
from driver.bootstrap_auth import *

ga = WxGather()


def search_Biz(kw: str = "", limit=5, offset=0):
    return ga.search_Biz(kw, limit, offset)


if __name__ == "__main__":
    pass
