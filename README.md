# 2026世界杯赛事对战+足彩赔率管理系统

## 项目简介

这是一个基于 **FastAPI + Vue3 + SQLite** 的 2026 世界杯赛事管理系统，包含以下功能：

- 小组赛赛程管理
- 淘汰赛赛程图
- 小组排名计算
- 小组第三晋级逻辑
- 足彩赔率管理（多数据源：体彩、API-Football、Mock）
- 响应式导航栏
- 现代化界面设计

## 技术栈

- **后端**：Python 3.12+, FastAPI 0.115, SQLModel 0.0.22, Pydantic v2, Uvicorn
- **前端**：Vue 3, Vite 5, Element Plus, Axios, Vue Router
- **数据库**：SQLite（单文件 `worldcup.db`）
- **其他**：uvicorn, pydantic-settings

## 项目结构

```
worldcup/
├── app/                              # FastAPI 应用包
│   ├── main.py                       # FastAPI app + lifespan
│   ├── config.py                     # Pydantic Settings 配置
│   ├── database.py                   # SQLModel engine + Session 依赖
│   ├── security.py                   # HTTPBearer 鉴权
│   ├── deps.py                       # 公共依赖
│   ├── models/                       # SQLModel 表模型
│   ├── routers/                      # FastAPI APIRouter
│   │   ├── matches.py                # /api/v1/matches
│   │   ├── groups.py                 # /api/v1/group_stage, /api/v1/rankings
│   │   ├── knockout.py               # /api/v1/knockout, /api/v1/knockout/bracket
│   │   ├── live.py                   # /api/v1/live/matches
│   │   ├── odds.py                   # /api/v1/odds/*
│   │   ├── flags.py                  # /api/v1/flags
│   │   └── admin.py                  # /api/v1/admin/* (Bearer 鉴权)
│   ├── services/                     # 业务逻辑
│   │   ├── match_service.py
│   │   ├── ranking_service.py
│   │   ├── knockout_service.py
│   │   ├── odds_service.py
│   │   ├── sporttery_provider.py
│   │   ├── odds_base.py
│   │   └── knockout_schema.py
│   └── utils/
│       ├── flags.py
│       └── normalize.py
├── config/
│   └── odds_providers.json           # 赔率数据源配置
├── frontend/                         # Vue3 SPA
│   ├── vite.config.js
│   └── src/
├── worldcup.db                       # SQLite 数据库
├── run.py                            # 启动入口（uvicorn）
├── start.sh                          # 一键启动脚本
├── requirements.txt
└── README.md
```

## 安装与运行

### 1. 克隆仓库

```bash
git clone <repo-url>
cd worldcup
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# Windows: venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务

**一键启动（前后端）：**

```bash
./start.sh
```

**分别启动：**

```bash
# 后端（FastAPI / uvicorn）
python run.py                       # 默认 http://127.0.0.1:5004
# 或：
uvicorn app.main:app --port 5004

# 前端（Vite dev server）
cd frontend && npm install && npm run dev
# 访问 http://127.0.0.1:5173
```

启动后：

- 后端 API：`http://127.0.0.1:5004`
- API 文档（Swagger UI）：`http://127.0.0.1:5004/docs`
- 前端页面：`http://127.0.0.1:5173`

## API 路由

| 路径 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| `/api/v1/matches?date=YYYY-MM-DD` | GET | - | 比赛列表 + 当日 + 后续 7 天 |
| `/api/v1/matches/{id}/result` | POST | - | 更新比赛比分 |
| `/api/v1/group_stage?group=X` | GET | - | 小组赛比赛（含体彩实时赔率） |
| `/api/v1/knockout` | GET | - | 淘汰赛比赛 |
| `/api/v1/knockout/bracket` | GET | - | 淘汰赛对阵图 |
| `/api/v1/rankings?group=X` | GET | - | 小组排名 |
| `/api/v1/flags` | GET | - | 国旗 emoji 映射 |
| `/api/v1/live/matches` | GET | - | 体彩当前在售比赛 |
| `/api/v1/odds/sources` | GET | - | 赔率数据源状态 |
| `/api/v1/odds/update` | POST | admin | 手动触发赔率更新 |
| `/api/v1/admin/groups` | GET | admin | 小组 + 队伍管理 |
| `/api/v1/admin/teams` | POST | admin | 添加队伍 |
| `/api/v1/admin/teams/{id}` | DELETE | admin | 删除队伍 |
| `/api/v1/admin/matches/generate` | POST | admin | 生成小组赛 |
| `/api/v1/admin/group_matches` | POST | admin | 手动添加小组赛 |
| `/api/v1/admin/matches` | GET | admin | 全部小组赛 |
| `/api/v1/admin/matches/{id}` | GET/PUT | admin | 单场比赛详情 / 更新 |

## 管理鉴权

`/api/v1/admin/*` 与 `/api/v1/odds/update` 需要 Bearer Token：

```bash
curl -H "Authorization: Bearer wc2026-admin-token" http://localhost:5004/api/v1/admin/groups
```

前端 axios 拦截器在 `src/api/index.js` 中对 `/admin/*` 和 `/odds/update` 自动添加 `Authorization: Bearer wc2026-admin-token`。

默认 Token：`wc2026-admin-token`（可通过环境变量 `ADMIN_TOKEN` 覆盖）。

## 数据兼容

- 数据库文件 `worldcup.db` 路径不变，迁移后继续使用原数据
- `create_all` 仅创建缺失表，不修改已有表结构
- 原 `schema.sql` 已被 SQLModel 表模型取代

## 系统功能

### 主页
- 显示当日比赛（含比分 / 赔率 / 提交比分表单）
- 显示往后赛程（按日期分组）

### 小组赛
- 按小组查看比赛
- 实时更新比赛结果

### 淘汰赛
- 显示淘汰赛赛程
- 淘汰赛赛程图（bracket view）

### 排名
- 显示小组排名
- 详细的队伍统计数据（积分、净胜球、进失球等）

### 管理
- 小组队伍管理
- 比赛管理
- 比赛生成

## 小组第三晋级逻辑

系统根据以下规则计算成绩最好的小组第三：

1. **积分**：3分/胜、1分/平
2. **净胜球**：总进球 - 总失球
3. **总进球数**

## 定时任务

后端在启动时执行一次赔率抓取；之后每隔 1 小时自动调用 `OddsCrawlerManager.update_database()`。任务通过 `lifespan` 钩子中的 `asyncio.create_task` 启动，与 FastAPI 进程同生命周期。

## 赔率数据源

通过 `config/odds_providers.json` 配置，示例：

```json
{
  "providers": {
    "sporttery": {
      "enabled": true,
      "priority": 1,
      "class": "SportteryProvider"
    },
    "api-football": {
      "enabled": false,
      "priority": 5,
      "class": "ApiFootballProvider",
      "api_key": "your-key"
    },
    "mock": {
      "enabled": true,
      "priority": 99,
      "class": "MockOddsProvider"
    }
  }
}
```

数字越小优先级越高。高优先级数据源的赔率会覆盖低优先级的同名比赛。

## 从旧版（Flask）迁移

如果你是从 `Flask + 模板渲染` 的旧版迁移过来：

1. 拉取最新代码
2. `pip install -r requirements.txt`（会自动卸载 Flask、安装 FastAPI）
3. 直接启动 `python run.py` 即可，旧 `worldcup.db` 数据自动保留

## 许可证

MIT License
