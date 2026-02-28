# 微信公众号订阅助手 - WebUI

基于Vue3 + Vite + ArcoDesign构建的前端界面

## 功能列表
- 用户登录/登出
- 文章列表展示
- 添加公众号订阅
- 修改用户信息
- 修改密码

## 手动安装依赖

由于系统限制，请按以下步骤手动安装依赖：

1. 打开PowerShell作为管理员
2. 运行以下命令更改执行策略：
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
3. 安装项目依赖：
```powershell
npm install
```
4. 安装ArcoDesign Vue：
```powershell
npm install --save @arco-design/web-vue @arco-design/web-vue-icon @arco-design/color
```
5. 安装开发依赖：
```powershell
npm install --save-dev less less-loader
```

## 环境变量配置

创建`frontend/.env.development`文件：
```ini
DEV_PROXY_TARGET=http://localhost:38001
VITE_APP_TITLE=微信公众号订阅助手
VITE_DEBUG_MODE=false
```

说明：
- 前端开发时统一请求相对路径（`/api/v1/`），由 Vite 代理转发到 `DEV_PROXY_TARGET`。
- 根目录 `.env` 是给 Docker Compose / 后端使用的，Vite 不会自动读取它。

## 运行项目

开发模式：
```bash
npm run dev
```

生产构建：
```bash
npm run build
```

## 项目结构

```
src/
├── api/                # API接口
├── assets/             # 静态资源
├── components/         # 公共组件
├── router/            # 路由配置
├── views/             # 页面组件
├── App.vue            # 根组件
└── main.ts            # 入口文件
```

## 技术栈
- Vue 3
- Vite
- ArcoDesign Vue
- TypeScript
- Axios
