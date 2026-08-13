# AIFriends

[English](README_EN.md) | **简体中文**

> 一个开源的 AI 角色创作与交互平台。用户可以创建角色、配置人格和音色，并通过文字或语音与角色持续对话。

在线演示：[https://app7804.acapp.acwing.com.cn/](https://app7804.acapp.acwing.com.cn/)

![AIFriends 项目截图](https://github.com/user-attachments/assets/5aea2de6-edbe-4649-adff-0104b3580a96)

## 项目简介

AIFriends 是一个面向学习、实验和开源协作的完整 LLM 应用。项目采用 Vue 3 与 Django 的前后端分离架构，通过 LangChain、LangGraph 和 OpenAI 兼容接口组织角色对话、工具调用、知识库检索与长期记忆，并通过流式接口同步返回文本和语音。

项目最初来自大模型应用开发课程，目前已重新进入维护阶段。现阶段优先保证部署可用、配置安全、测试可重复，并逐步改善新贡献者体验。

## 当前能力

- 角色创建、编辑、删除、分享与好友管理
- 角色头像、聊天背景、人格描述、系统提示词和音色配置
- 基于 `deepseek-v4-flash-202605` 的流式角色对话
- LangGraph 工具调用：当前包含时间查询与 LanceDB 知识库检索
- 最近对话上下文与角色长期记忆更新
- JWT 登录、注册、刷新令牌和用户资料管理
- 阿里云实时语音识别（ASR）
- 腾讯云流式文本语音合成（TTS），兼容已有阿里云音色
- 可重复执行的官方演示内容初始化命令

## 2026 年 8 月维护更新

本轮维护完成了以下改进：

- 接入腾讯云流式文本语音合成，支持签名鉴权、READY/FINAL 事件和 MP3 音频分片回传。
- 保留旧音色兼容规则：`tencent:<VoiceType>` 使用腾讯云，`aliyun:<voice>` 和无前缀旧数据继续使用阿里云。
- 将角色对话与记忆模型切换到 TokenHub 当前可用的 `deepseek-v4-flash-202605`。
- 增加 4 个官方演示角色、4 个腾讯云音色、默认头像、角色图片和基础系统提示词。
- 修复前端构建后静态模板更新脚本在 ESM 项目中的执行问题。
- 增加模型配置、腾讯云 TTS 协议和演示数据幂等性测试；当前后端测试共 14 项。
- 已在腾讯云服务器完成部署验证，并对真实模型调用、真实腾讯云 MP3 合成和公网访问进行验收。

详细说明：

- [腾讯云流式语音合成接入指南](docs/tencent-cloud-tts.md)
- [官方演示内容维护说明](docs/demo-content.md)

## 技术栈

### 前端

- Vue 3.5
- Vite 7
- Vue Router 4
- Pinia 3
- Tailwind CSS 4 + daisyUI 5
- Axios、VAD Web

### 后端与 AI

- Python 3.12+
- Django 6 + Django REST Framework
- Simple JWT
- LangChain + LangGraph
- OpenAI 兼容模型接口（当前使用腾讯云 TokenHub）
- LanceDB 向量存储
- SQLite
- WebSocket + Server-Sent Events

### 外部服务

- 腾讯云 TokenHub：角色对话和长期记忆模型
- 腾讯云语音合成：流式 MP3 TTS
- 阿里云 DashScope：实时 ASR，并兼容原有 TTS/音色管理流程

## 架构概览

```text
Browser
  │
  ├─ Vue 3 SPA
  │    ├─ REST API：认证、角色、好友、历史消息
  │    └─ SSE：对话文本与 Base64 MP3 音频分片
  │
  └─ Django + DRF
       ├─ LangGraph：角色提示词、近期消息、工具调用
       ├─ OpenAI-compatible API：DeepSeek 模型
       ├─ LanceDB：知识库检索
       ├─ Tencent Cloud TTS / Aliyun ASR
       └─ SQLite + media：业务数据与用户图片
```

## 项目结构

```text
AIFriends/
├── backend/
│   ├── backend/                  # Django 配置与入口
│   ├── web/
│   │   ├── management/commands/ # 演示内容初始化命令
│   │   ├── demo_assets/         # 官方演示角色与默认图片
│   │   ├── documents/           # 知识库数据与 LanceDB 逻辑
│   │   ├── models/              # 用户、角色、好友、消息等模型
│   │   ├── views/               # REST、SSE、ASR、TTS 和 AI 图
│   │   └── test_*.py            # 后端测试
│   ├── media/                   # 用户上传文件（不提交到 Git）
│   ├── static/                  # Vite 构建输出
│   └── manage.py
├── frontend/
│   ├── src/components/          # 通用组件
│   ├── src/views/               # 页面与业务组件
│   ├── src/router/              # 路由
│   ├── src/stores/              # Pinia 状态
│   └── src/js/                  # API 与运行环境配置
├── docs/                        # 接入与维护文档
├── Lessons/                     # 课程学习记录
├── scripts/                     # uWSGI 与构建辅助脚本
├── nginx.conf                   # Nginx 配置示例
└── deploy-frontend.ps1          # Windows 前端部署脚本
```

## 本地开发

### 环境要求

- Python 3.12+
- Node.js 20.19+ 或 22.12+
- npm

### 1. 克隆仓库

```bash
git clone https://github.com/ppshuX/AIFriends.git
cd AIFriends
```

### 2. 配置后端

```bash
cd backend
python -m venv .venv
```

激活虚拟环境：

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

安装依赖并初始化数据库：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
```

在 `backend/.env` 中配置所需服务。真实密钥不得提交到 Git：

```dotenv
# TokenHub / OpenAI-compatible chat API
API_BASE=https://tokenhub.tencentmaas.com/v1
API_KEY=replace-with-your-api-key

# Aliyun realtime ASR and legacy TTS
WSS_URL=replace-with-your-dashscope-websocket-url

# Required when using tencent:<VoiceType>
TENCENT_TTS_APP_ID=replace-with-your-app-id
TENCENT_TTS_SECRET_ID=replace-with-your-secret-id
TENCENT_TTS_SECRET_KEY=replace-with-your-secret-key
```

可选：安装官方演示内容。命令可以重复执行，不会删除其他用户数据。

```bash
python manage.py seed_demo_content
```

启动后端：

```bash
python manage.py runserver
```

### 3. 配置前端

打开 `frontend/src/js/config/config.js`，本地前后端分离开发时将：

```js
const platform = 'cloud'
```

改为：

```js
const platform = 'vue'
```

然后启动 Vite：

```bash
cd ../frontend
npm ci
npm run dev
```

访问 [http://localhost:5173/](http://localhost:5173/)。Django 默认运行在 `http://127.0.0.1:8000/`。

### 4. 构建前端

```bash
cd frontend
npm run build
```

构建产物写入 `backend/static/frontend/`。`postbuild` 会运行 `scripts/update-django-static.cjs`，自动更新 Django SPA 模板中的静态资源引用。

## 测试

运行完整后端测试：

```bash
cd backend
python manage.py test web --verbosity 2
```

单独验证本轮维护功能：

```bash
python manage.py test web.test_model_configuration --verbosity 2
python manage.py test web.test_tencent_tts --verbosity 2
python manage.py test web.test_seed_demo_content --verbosity 2
```

前端生产构建检查：

```bash
cd frontend
npm ci
npm run build
```

测试中的腾讯云 TTS 用例使用模拟 WebSocket，不会访问云服务，也不需要真实密钥。真实联调会产生云服务用量。

## 部署说明

当前在线实例运行在腾讯云服务器。仓库中的 `nginx.conf`、`scripts/uwsgi.ini` 和 `deploy-frontend.ps1` 是部署参考，不是一键部署方案；使用前需按服务器路径、域名和进程管理方式调整。

推荐的生产流程：

1. 安装后端依赖，执行数据库迁移。
2. 构建前端并执行 `python manage.py collectstatic --noinput`。
3. 将 `db.sqlite3`、`media/` 和 LanceDB 数据放入持久化存储，并在更新前备份。
4. 通过服务器环境变量、只读 `.env` 或密钥管理服务注入凭据。
5. 使用 Gunicorn/uWSGI 托管 Django，由 Nginx 提供 HTTPS、静态文件和媒体文件。
6. 部署后检查首页、登录、角色对话、模型调用和真实 TTS 音频。

## 已知边界与安全提醒

- `backend/backend/settings.py` 仍保留课程开发配置，包括 `DEBUG = True`、示例 `SECRET_KEY` 和固定域名。公开部署前必须改为环境变量配置并运行 `python manage.py check --deploy`。
- SQLite 适合本地开发和小规模演示。多实例或高并发部署应评估 PostgreSQL/MySQL 与独立对象存储。
- 腾讯云实现目前支持数字 `VoiceType` 预置音色，不支持声音复刻产生的 `FastVoiceType`。
- 知识库示例内容和默认角色提示词仅用于演示，正式社区需要补充内容安全、隐私与未成年人保护规则。
- 云服务会产生用量和费用。请设置资源包提醒、调用限制和最小权限子账号，并定期轮换密钥。

## 贡献

欢迎提交 Issue 和 Pull Request。建议在提交前完成：

```bash
cd backend
python manage.py test web --verbosity 2

cd ../frontend
npm ci
npm run build
```

提交应围绕一个可验证的问题，说明变更原因、测试方法和用户影响。不要提交 `.env`、数据库、媒体文件、IDE 配置或云服务密钥。

## 许可证

AIFriends 使用 [MIT License](LICENSE) 开源。
