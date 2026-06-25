# Moola - 智能与协同记账共享账本

**简体中文** | [English](README.md)

Moola 是一款现代化、响应式的智能记账应用，既适用于个人财务收支管理，也支持多人的团队/项目协同记账（例如：合租生活分摊、旅行账单管理、团队预算等）。

---

## 🚀 核心特性

* **个人账本管理**：直观清爽的收支流向展示。大额交易（如 10W 以上）支持动态缩写（展示“w”、“b”等记数单位）及鼠标悬浮展示具体金额。
* **团队/项目协同账本**：支持团队成员加入共享项目账套，协同记录收支，自动结算并展示成员间的结余账单。
* **智能分类系统**：预置高频系统分类（餐饮、购物、工资、兼职等），支持自定义分类，提供精美调色板和现代化 Lucide 图标。
* **多张图片上传**：每笔记账记录支持上传最多 6 张收据照片或截图。
* **高端图片预览组件**：独立的图片画廊组件，支持手势或鼠标拖拽平移、滚轮/双指缩放、旋转、镜像翻转、快速下载以及复制图片地址等。
* **优化的 HTTP 静态文件缓存**：静态文件资源具备强缓存响应头 `Cache-Control`（缓存 1 年）及基于 ETag（`If-None-Match` 返回 `304 Not Modified`）的协商缓存。
* **自动过期的数据库缓存（TTL）**：通过 MongoDB TTL 索引对上传文件设置 30 天自动过期策略，文件每次被访问时会通过后台任务自动续期 30 天。

---

## 🛠️ 技术栈

* **前端**：Vue 3 (Composition API)、Vite、Element Plus、Pinia (状态管理)、Vue Router、TailwindCSS / Vanilla CSS、Lucide Vue Icons。
* **后端**：FastAPI (Python 3.11+)、Motor (异步 MongoDB 驱动)、Pydantic (V2)、PyJWT、python-multipart。
* **数据库**：MongoDB (6.0+)。

---

## 🐳 部署方案 1：Docker Compose 一键部署（推荐）

这是将整个系统（前端、后端、数据库）部署到云服务器或本地机器上最简单快捷的方式。Docker 容器中的端口与宿主机上的端口保持一致。

### 1. 配置端口
在项目根目录（`docker-compose.yml` 旁）创建一个 `.env` 文件：
```env
FRONTEND_PORT=9090
BACKEND_PORT=9080
```

### 2. 启动服务
在项目根目录下执行以下命令：
```bash
docker compose up --build -d
```

### 3. 验证与访问
* **Web UI (前端)**：通过浏览器访问 `http://<您的服务器IP>:9090`。
* **API (后端)**：已配置 Nginx 代理，前端发出的 `/api/*` 请求将自动被代理转发至容器内后端服务的 `9080` 端口。
* **数据库 (MongoDB)**：运行在宿主机的 `27017` 端口上（数据保存在本地命名卷 `mongo_data` 中）。

*(注：如果是在云服务器部署，请确保您的云控制台安全组已放行 `9090` 和 `9080` 端口。正常应用使用仅需放行 `9090` 端口即可)。*

---

## 💻 部署方案 2：独立手动启动服务

如果您希望分别启动后端和前端服务以便于开发调试，请按照以下步骤操作。

### 环境要求
* **MongoDB**：已安装并运行在 `mongodb://localhost:27017`。
* **Python**：3.11+ 版本。
* **Node.js**：18.0+ 版本。

---

### 步骤 A：后端服务启动

1. **进入后端文件夹**：
   ```bash
   cd backend
   ```

2. **创建并激活虚拟环境**：
   ```bash
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **安装 Python 依赖项**：
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**：
   在 `backend` 目录下创建 `.env` 文件：
   ```env
   PROJECT_NAME=Moola
   MONGODB_URL=mongodb://localhost:27017
   DATABASE_NAME=moola_db
   JWT_SECRET=super-secret-key-moola-bookkeeping-app-2026
   ACCESS_TOKEN_EXPIRE_DAYS=30
   JWT_ALGORITHM=HS256
   HOST=0.0.0.0
   PORT=8000
   RELOAD=True
   ```

5. **启动后端服务**：
   ```bash
   python main.py
   ```
   后端服务启动在 `http://localhost:8000`。系统内置的分类和数据库索引会在首次启动时自动加载。

---

### 步骤 B：前端服务启动

1. **进入前端文件夹**：
   ```bash
   cd frontend
   ```

2. **安装 Node 模块依赖**：
   ```bash
   npm install
   ```

3. **配置环境变量**：
   在 `frontend` 目录下创建 `.env` 文件：
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. **启动开发服务器**：
   ```bash
   npm run dev
   ```
   前端应用启动在 `http://localhost:5173`。

5. **打包生产版本静态资源**：
   ```bash
   npm run build
   ```
   构建输出的代码将保存在 `dist/` 文件夹中，可以通过任何静态网页服务器（如 Nginx）进行托管。
