# 2026世界杯赛事对战+足彩赔率管理系统

## 项目简介

这是一个基于Flask的2026世界杯赛事管理系统，包含以下功能：

- 小组赛赛程管理
- 淘汰赛赛程图
- 小组排名计算
- 小组第三晋级逻辑
- 足彩赔率管理
- 响应式导航栏
- 现代化界面设计

## 技术栈

- **后端**：Python 3.12, Flask 2.0.1
- **前端**：HTML5, CSS3, Bootstrap 5.3.0, JavaScript
- **数据库**：SQLite
- **其他**：Git, GitHub

## 项目结构

```
worldcup-2026/
├── app.py                # 主应用文件
├── schema.sql            # 数据库结构
├── import_schedule.py    # 赛程导入脚本
├── crawler.py            # 爬虫模块
├── check_data.py         # 数据检查脚本
├── requirements.txt      # 依赖文件
├── .gitignore            # Git忽略文件
├── templates/            # 模板文件
│   ├── index.html        # 主页
│   ├── group_stage.html  # 小组赛
│   ├── knockout.html     # 淘汰赛
│   ├── knockout_bracket.html  # 淘汰赛赛程图
│   ├── rankings.html     # 排名页面
│   └── admin/            # 管理页面
└── crawler/              # 爬虫模块
    └── odds_crawler.py   # 赔率爬虫
```

## 功能特点

### 1. 小组赛管理
- 支持查看每个小组的比赛安排
- 实时更新比赛结果
- 自动计算小组排名

### 2. 淘汰赛赛程图
- 可视化的淘汰赛赛程树状图
- 自动显示小组晋级队伍
- 支持小组第三的比较逻辑（积分、净胜球、总进球数）

### 3. 排名系统
- 实时计算小组排名
- 显示详细的队伍统计数据（积分、净胜球、进失球等）

### 4. 赔率管理
- 自动爬取和更新比赛赔率
- 显示最新赔率信息

### 5. 管理功能
- 小组队伍管理
- 比赛管理
- 比赛生成

## 安装与运行

### 1. 克隆仓库

```bash
git clone https://github.com/Charlielian/worldcup-2026.git
cd worldcup-2026
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
# 激活虚拟环境
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
python app.py
```

### 5. 导入赛程数据

```bash
python import_schedule.py
```

### 6. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5001` 上运行

## 系统功能

### 主页
- 显示当日比赛
- 显示往后赛程
- 支持日期选择

### 小组赛
- 按小组查看比赛
- 实时更新比赛结果

### 淘汰赛
- 显示淘汰赛赛程
- 淘汰赛赛程图

### 排名
- 显示小组排名
- 详细的队伍统计数据

### 管理
- 小组队伍管理
- 比赛管理
- 比赛生成

## 小组第三晋级逻辑

系统根据以下规则计算成绩最好的小组第三：

1. **积分**：3分/胜、1分/平
2. **净胜球**：总进球 - 总失球
3. **总进球数**

## 技术实现

### 数据库设计
- `groups`：小组信息
- `teams`：队伍信息
- `matches`：比赛信息
- `knockout_matchups`：淘汰赛对阵
- `odds`：赔率信息

### 核心功能
- `get_group_rankings()`：计算小组排名
- `get_best_third_place_teams()`：计算成绩最好的小组第三
- `update_knockout_teams()`：更新淘汰赛队伍
- `get_knockout_bracket_data()`：获取淘汰赛赛程图数据

## 项目亮点

1. **现代化界面**：使用Bootstrap 5.3.0和自定义CSS实现响应式设计
2. **实时数据**：自动爬取和更新比赛赔率
3. **智能计算**：自动计算小组排名和晋级队伍
4. **可视化赛程图**：直观的淘汰赛赛程树状图
5. **完整的管理功能**：支持队伍和比赛的管理

## 未来计划

- 增加用户认证系统
- 添加更多数据可视化功能
- 支持更多赛事数据
- 优化移动端体验

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

- GitHub: [Charlielian](https://github.com/Charlielian)
- Email: your.email@example.com
