from core.common.app_settings import settings
from jobs.notice import sys_notice
from driver.wx.service import get_qr_code, get_state
import time


def send_wx_code(title: str = "", url: str = ""):
    if settings.send_code:
        # 迁移：统一走 wx_service，对外不再依赖 success.py 的回调
        get_qr_code(notice=CallBackNotice)
    return


def CallBackNotice():
    st = get_state()
    url = st.get("wx_login_url")
    svg = """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
        <rect x="10" y="10" width="180" height="180" fill="#ffcc00" stroke="#000" stroke-width="2"/>
        </svg>
        """
    url = str(url)
    text = f"- 服务名：{settings.server_name}\n"
    text += (
        f"- 发送时间： {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))}"
    )
    if st.get("has_code"):
        text += f"![二维码]({url})"
        text += f"\n- 请使用微信扫描二维码进行授权"
    sys_notice(text, settings.code_title or "WxHarvester授权过期,扫码授权")
