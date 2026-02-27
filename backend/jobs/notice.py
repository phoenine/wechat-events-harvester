from core.common.app_settings import settings
import time


def sys_notice(text: str = "", title: str = "", tag: str = "系统通知", type=""):
    from core.integrations.notice import notice

    markdown_text = f"### {title} {type} {tag}\n{text}"
    webhook = settings.notice_dingding
    if len(webhook) > 0:
        notice(webhook, title, markdown_text)
    feishu_webhook = settings.notice_feishu
    if len(feishu_webhook) > 0:
        notice(feishu_webhook, title, markdown_text)
    wechat_webhook = settings.notice_wechat
    if len(wechat_webhook) > 0:
        notice(wechat_webhook, title, markdown_text)
    custom_webhook = settings.notice_custom
    if len(custom_webhook) > 0:
        notice(custom_webhook, title, markdown_text)
