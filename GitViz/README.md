# GitViz — Git Repository Visualizer

> AI 驱动的多 Agent 协作项目，将 Git 仓库管理从命令行迁移到可视化界面。
>
> 本项目是使用 Claude (Anthropic) 进行 AI 驱动开发的成果，展示了多 Agent 协作、长链推理和工具使用的完整流程。

## 功能一览

| 功能 | 说明 |
|------|------|
| 📂 **本地仓库浏览** | 输入路径即可打开任意本地 Git 仓库，自动检测 |
| 📜 **提交历史可视化** | 时间线形式展示所有提交，分支标签高亮，合并提交标识 |
| 🌿 **分支管理** | 查看所有本地/远程分支，一键切换 |
| 📋 **工作区状态** | 可视化显示 git status，区分已暂存/未暂存/未跟踪 |
| 📦 **下载压缩包** | 任意提交可一键打包为 ZIP 下载 |
| ⏪ **版本回退** | 支持 soft / mixed / hard 三种回退模式，带确认机制 |
| 🔄 **实时刷新** | 一键刷新所有视图，保持与仓库同步 |
| 🔍 **提交 Diff 查看** | 滑入面板展示提交详情、文件变更、代码差异 |

## 快速开始

### 1. 安装依赖

```bash
pip install flask
```

### 2. 创建测试仓库（可选）

```bash
# macOS / Linux
bash setup_demo_repo.sh

# Windows (PowerShell)
.\setup_demo_repo.ps1
```

### 3. 启动 GitViz

```bash
python app.py
```

### 4. 打开浏览器

访问 http://localhost:5000

在欢迎界面输入你的仓库路径（或测试仓库路径），点击"打开仓库"即可。

## 项目结构

```
GitViz/
├── app.py                 # Flask 后端 API
├── git_ops.py             # Git 操作封装（subprocess）
├── requirements.txt       # 依赖：flask
├── setup_demo_repo.sh     # 测试仓库创建脚本 (macOS/Linux)
├── setup_demo_repo.ps1    # 测试仓库创建脚本 (Windows)
├── templates/
│   └── index.html         # 单页前端应用（深色主题）
└── README.md
```

## 技术架构

### 前后端分离

```
浏览器 UI  ←→  Flask API (app.py)  ←→  Git 操作层 (git_ops.py)  ←→  本地 Git 仓库
(HTML/CSS/JS)                    (RESTful JSON)                (subprocess)
```

### 多 Agent 协作设计

本项目由多个 AI Agent 协作构建：

| Agent | 职责 |
|-------|------|
| **架构 Agent** | 设计整体架构、技术选型、API 规划 |
| **后端 Agent** | 实现 git_ops.py 操作封装、Flask 路由 |
| **前端 Agent** | 构建深色主题 UI、时间线、交互逻辑 |
| **测试 Agent** | 创建测试仓库、验证功能完整性 |
| **文档 Agent** | 编写文档、申请文案整理 |

## 申请相关信息

本项目可作为 AI 驱动开发能力的证明，包含：

- **问题 04 成果描述**：多 Agent 协作实现 Git 可视化工具
- **问题 05 使用证明**：项目完整代码 + 运行截图 + 终端日志

详见申请文案文档。

## 技术亮点

- **单页应用**：Flask 后端 + 原生 JavaScript 前端，零前端框架依赖
- **深色主题**：GitHub 风格暗色 UI，专业视觉体验
- **安全操作**：回退操作带双重确认，硬回退有明确警告
- **实时同步**：前端操作后自动刷新所有视图
- **错误处理**：全链路错误捕获，用户友好的 Toast 提示
