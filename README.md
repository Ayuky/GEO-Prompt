# GEO Prompt 优化系统

基于强化学习的GEO Prompt优化平台，集成若依后台管理系统与Langfuse LLM可观测性。

## 系统架构

```
┌──────────────────────────────────────────────────────┐
│                    Nginx :80                         │
│                     若依前端                         │
└──────────┬──────────────────────────┬────────────────┘
           │ /prod-api                │
┌──────────▼──────────┐    ┌──────────▼────────────────┐
│  RuoYi Backend      │    │  GeoPrompt Backend        │
│  Spring Boot :8080  │    │  FastAPI :8000            │
└──────────┬──────────┘    └──────────┬────────────────┘
           │                          │
┌──────────▼──────────────────────────▼────────────────┐
│              MySQL :3306 (ry-vue)                    │
└──────────────────────────┬───────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────┐
│              Redis :6379                             │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                  Langfuse :3000                      │
│     (Postgres · ClickHouse · MinIO · Redis)          │
└──────────────────────────────────────────────────────┘
```

| 服务 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| ruoyi-frontend | Vue 2 + Nginx | 80 | 前端管理界面 |
| ruoyi-backend | Spring Boot 4 + MyBatis | 8080 | 后端 API |
| geoprompt | Python FastAPI | 8000 | RL Prompt 优化引擎 |
| mysql | MySQL 8.0 | 3306 | 共享数据库 |
| redis | Redis 7 | 6379 | 共享缓存 |
| langfuse-web | Next.js | 3000 | LLM 可观测面板 |
| langfuse-* | Postgres/ClickHouse/MinIO | — | Langfuse 配套服务 |

## 快速启动

### 环境要求

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / Mac) 或 Docker Engine 24+
- 确保以下端口未被占用：`80` `8080` `8000` `3306` `6379` `3000` `5432`

### 一键启动

```bash
# 克隆仓库
git clone <repo-url> && cd GEO

# 复制环境变量（按需修改密码和密钥）
cp .env.example .env

# 启动核心服务（RuoYi + GeoPrompt）
docker compose --profile core up -d

# 查看构建/启动日志
docker compose --profile core logs -f
```

启动后访问：
- **管理后台**：http://localhost （默认 admin / admin123）
- **GeoPrompt API**：http://localhost:8000/docs
- **Druid 监控**：http://localhost/druid （ruoyi / 123456）

### 启动 Langfuse（可选）

```bash
docker compose --profile langfuse up -d
```

访问 http://localhost:3000

### 全部启动

```bash
docker compose --profile full up -d
```

### 停止

```bash
# 停止服务（保留数据卷）
docker compose --profile full down

# 停止并删除数据卷（重置数据库）
docker compose --profile full down -v
```

## 数据初始化

首次启动时 MySQL 容器会自动执行 [RuoYi-Vue/sql/](RuoYi-Vue/sql/) 目录下的 SQL 文件，完成建表和初始数据导入。
如需手动操作数据库：
可以通过宿主机端口 `localhost:3306` 使用 DBeaver / Navicat 等工具直接连接。

## 常用命令

```bash
# 查看运行状态
docker compose --profile full ps

# 查看指定服务日志
docker compose logs -f ruoyi-backend
docker compose logs -f geoprompt

# 重启单个服务
docker compose --profile core restart ruoyi-backend

# 重新构建并启动（代码修改后）
docker compose --profile core up -d --build geoprompt
docker compose --profile core up -d --build ruoyi-backend
docker compose --profile core up -d --build ruoyi-frontend

docker compose --profile full up -d --build
```

## 项目目录

```
GEO/
├── docker-compose.yml          # 容器编排
├── .env                        # 环境变量
├── GeoPrompt/                  # Python RL 优化引擎
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── api/v1/             # API 路由
│   │   ├── core/               # 配置/数据库
│   │   ├── models/             # ORM 模型
│   │   ├── services/           # 业务逻辑
│   │   └── rl/                 # 强化学习
│   └── requirements.txt
├── RuoYi-Vue/                  # 若依后台管理
│   ├── Dockerfile              # Spring Boot 后端
│   ├── ruoyi-admin/            # 管理模块
│   ├── ruoyi-system/           # 业务模块
│   ├── ruoyi-framework/        # 框架模块
│   ├── ruoyi-common/           # 通用工具
│   ├── sql/                    # 数据库初始化脚本
│   └── ruoyi-ui/               # Vue 前端
│       ├── Dockerfile
│       └── nginx.conf
└── Langfuse/                   # LLM 可观测
```

## 开发说明

代码修改后重建对应服务即可，无需重启整个集群：

```bash
# Python 代码变更 → 重建 geoprompt
docker compose --profile core up -d --build geoprompt

# Java 代码变更 → 重建 ruoyi-backend
docker compose --profile core up -d --build ruoyi-backend

# 前端代码变更 → 重建 ruoyi-frontend
docker compose --profile core up -d --build ruoyi-frontend
```

容器内服务通过容器名互相访问（如 `mysql`、`redis`、`geoprompt`），无需关心 IP 地址。
