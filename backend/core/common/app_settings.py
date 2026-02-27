from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except Exception:
        return default


@dataclass(frozen=True)
class AppSettings:
    app_name: str
    server_name: str
    web_name: str
    send_code: bool
    code_title: str
    enable_job: bool
    auto_reload: bool
    threads: int
    port: int
    debug: bool
    log_level: str
    log_file: str
    cache_dir: str
    local_avatar: bool
    avatar_max_bytes: int
    safe_lic_key: str
    webhook_content_format: str
    user_agent: str
    notice_dingding: str
    notice_wechat: str
    notice_feishu: str
    notice_custom: str


def load_app_settings() -> AppSettings:
    return AppSettings(
        app_name=os.getenv("APP_NAME", "wx-harvester"),
        server_name=os.getenv("SERVER_NAME", "wx-harvester"),
        web_name=os.getenv("WEB_NAME", "WxHarvester微信公众号采集助手"),
        send_code=_as_bool(os.getenv("SEND_CODE"), True),
        code_title=os.getenv("CODE_TITLE", "WxHarvester"),
        enable_job=_as_bool(os.getenv("ENABLE_JOB"), True),
        auto_reload=_as_bool(os.getenv("AUTO_RELOAD"), False),
        threads=max(1, _as_int(os.getenv("THREADS"), 1)),
        port=_as_int(os.getenv("PORT"), 38001),
        debug=_as_bool(os.getenv("DEBUG"), False),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_file=os.getenv("LOG_FILE", "./data/logs/wx-harvester.log"),
        cache_dir=os.getenv("CACHE_DIR", "data/cache"),
        local_avatar=_as_bool(os.getenv("LOCAL_AVATAR"), False),
        avatar_max_bytes=_as_int(os.getenv("AVATAR_MAX_BYTES"), 5 * 1024 * 1024),
        safe_lic_key=os.getenv("SAFE_LIC_KEY", "PHOENINE-SECURE-LIC-KEY-1234567890"),
        webhook_content_format=os.getenv("WEBHOOK_CONTENT_FORMAT", "html"),
        user_agent=os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36/WeRss",
        ),
        notice_dingding=os.getenv("DINGDING_WEBHOOK", ""),
        notice_wechat=os.getenv("WECHAT_WEBHOOK", ""),
        notice_feishu=os.getenv("FEISHU_WEBHOOK", ""),
        notice_custom=os.getenv("CUSTOM_WEBHOOK", ""),
    )


settings = load_app_settings()
