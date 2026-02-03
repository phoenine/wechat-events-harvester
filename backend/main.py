import threading
import asyncio
import uvicorn

from dotenv import load_dotenv
load_dotenv()

from core.common.config import cfg
from core.common.print import print_warning


if __name__ == "__main__":
    if cfg.args.init == "True":
        import init_sys as init

        asyncio.run(init.init())
    if cfg.args.job == "True" and cfg.get("server.enable_job", False):
        from jobs import start_all_task

        threading.Thread(target=start_all_task, daemon=False).start()
    else:
        print_warning("未开启定时任务")
    print("启动服务器")
    AutoReload = cfg.get("server.auto_reload", False)
    thread = cfg.get("server.threads", 1)
    uvicorn.run(
        "web:app",
        host="0.0.0.0",
        port=int(cfg.get("port", 38001)),
        reload=AutoReload,
        reload_dirs=["core", "web_ui"],
        reload_excludes=["web_ui", "data"],
        workers=thread,
    )
    pass
