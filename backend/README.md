# WeRSS Backend

微信公众号文章采集与订阅后端服务，基于 FastAPI + Supabase + Playwright。

## 1. 项目定位

本项目负责以下能力：

- 公众号检索、订阅管理、文章采集
- 文章内容清洗与导出（HTML/PDF/Markdown）
- 登录授权（二维码登录状态管理）
- 消息任务（定时采集 + Webhook 通知）
- 标签、事件、配置管理等后台接口

## 2. 技术栈

- Python 3.13（Docker 镜像内使用 3.13.1）
- FastAPI + Uvicorn
- Supabase（Auth / Database / Storage）
- Playwright（公众号相关抓取流程）
- APScheduler（定时任务）
- Loguru（统一日志门面）

## 3. 目录结构

```text
backend/
├── apis/                     # HTTP API 路由层
├── core/                     # 领域逻辑与基础能力
│   ├── integrations/         # Supabase/Wx/通知等基础设施适配
│   ├── common/               # 配置、日志、任务队列等通用组件
│   ├── articles|feeds|...    # 各业务领域仓储与模型
├── driver/                   # 浏览器与会话驱动层（Playwright/Wx）
├── jobs/                     # 定时任务与异步任务编排
├── ops/                      # 运维脚本与迁移相关
├── devtools/                 # 本地调试/辅助开发脚本
├── main.py                   # 进程启动入口
├── web.py                    # FastAPI 应用入口
└── .env                      # 运行环境变量配置
```

## 4. 运行前准备

### 4.1 系统依赖

- 安装 Python 3.13
- 安装浏览器依赖（Playwright 运行需要）

### 4.2 Python 依赖

```bash
pip install -r requirements.txt
playwright install
playwright install firefox
```

### 4.3 配置

请配置 `.env`（或系统环境变量）：

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `PORT` / `LOG_LEVEL` / `LOG_FILE`
- `ENABLE_JOB` / `AUTO_RELOAD` / `THREADS`
- `USERNAME` / `PASSWORD`（初始化管理员账号）

## 5. 启动方式

### 5.1 本地启动

初始化用户（幂等）：

```bash
python init_sys.py
```

启动服务：

```bash
python main.py
```

若需同时启用定时任务与初始化参数：

```bash
python main.py -job True -init True
```

### 5.2 Docker 启动

项目包含 `Dockerfile` 与 `entrypoint.sh`，默认会执行：

```bash
python main.py -job True -init True
```

## 6. API 文档

服务启动后可访问：

- Swagger: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI: `/api/openapi.json`

默认 API 前缀：`/api/v1/wx`

## 7. 核心接口分组

- `auth`：认证与二维码授权
- `user`：用户资料与头像
- `wechat-accounts`：公众号管理与采集触发（兼容旧路径 `mps`）
- `article`：文章查询与清理
- `message_tasks`：消息任务管理
- `configs`：配置管理
- `tags`：标签管理
- `events`：事件管理
- `sys`：系统信息

## 8. 日志与任务

- 日志统一走 `core.common.log`（Loguru）
- 应用启动时会拉起任务队列（`TaskQueue`）
- 定时任务由 `jobs/` + `APScheduler` 驱动

## 9. 常见开发命令

语法检查：

```bash
python -m compileall .
```

查看路由相关实现：

```bash
rg "APIRouter\\(|@router" apis
```

## 10. 注意事项

- Playwright 与会话状态对抓取流程影响较大，建议在稳定网络和固定环境下运行。
- 生产环境请显式配置 CORS 白名单、Supabase 凭据与通知 Webhook。
- 若启用会话落库，请先创建 `sql/auth_sessions.sql` 对应表结构。
