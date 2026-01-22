# AIFriends - 虚拟女友/男友/朋友创作分享平台

> 一个大模型应用入门项目，支持用户创建并分享虚拟角色，实现语音交互和智能对话

## 📖 项目简介

AIFriends 是一个基于大语言模型的虚拟角色创作分享平台。用户可以创建任意多个虚拟女友/男友/朋友，自定义角色音色、性格、简介，并通过语音识别、语音合成、语音复刻等技术实现与虚拟人物的语音通话交流。

本项目采用前后端分离架构，后端使用 Django，前端使用 Vue3，大模型框架采用 LangChain。

## ✨ 功能特性

- 🎭 **角色创建与管理**：支持创建并分享任意多个虚拟角色，可自定义音色、性格、简介
- 🎤 **语音交互**：支持语音识别、语音合成、语音复刻，实现与虚拟人物语音通话交流
- 🤖 **智能对话**：基于大语言模型的智能对话系统
- 🔧 **Function Call**：支持函数调用功能
- 📚 **知识库**：支持知识库功能
- 🔐 **用户认证**：基于 JWT 的用户认证系统
- 🌐 **跨域支持**：配置了 CORS 跨域资源共享

## 🛠️ 技术栈

### 后端
- **框架**：Django 6.0.1
- **认证**：Django REST Framework + Simple JWT
- **大模型框架**：LangChain
- **数据库**：SQLite（开发环境）
- **跨域**：django-cors-headers

### 前端
- **框架**：Vue 3.5.26
- **构建工具**：Vite 7.3.0
- **路由**：Vue Router 4.6.4
- **状态管理**：Pinia 3.0.4

## 📁 项目结构

```
AIFriends/
├── backend/                 # Django 后端项目
│   ├── backend/            # Django 项目配置
│   │   ├── settings.py     # 项目设置
│   │   ├── urls.py         # 主 URL 配置
│   │   └── ...
│   ├── web/                # Web 应用
│   │   ├── views/          # 视图函数
│   │   │   └── index.py   # 首页视图
│   │   ├── templates/      # 模板文件
│   │   │   └── index.html # 前端入口模板
│   │   ├── urls.py         # URL 路由
│   │   └── models.py       # 数据模型
│   ├── static/             # 静态文件目录
│   │   └── frontend/       # 前端构建产物
│   ├── manage.py           # Django 管理脚本
│   └── db.sqlite3          # SQLite 数据库
├── frontend/               # Vue3 前端项目
│   ├── src/                # 源代码目录
│   │   ├── components/     # Vue 组件
│   │   ├── views/          # 页面视图
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # Pinia 状态管理
│   │   └── main.js         # 入口文件
│   ├── public/             # 公共资源
│   ├── package.json        # 依赖配置
│   └── vite.config.js      # Vite 配置
└── README.md               # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 20.19.0+ 或 22.12.0+
- npm 或 yarn

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd AIFriends
```

#### 2. 后端设置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install django==6.0.1
pip install djangorestframework
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install langchain
# 根据实际需求安装其他依赖

# 运行数据库迁移
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser
```

#### 3. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 构建前端项目（生产环境）
npm run build

# 将构建产物复制到后端 static 目录
# Windows:
xcopy /E /I dist\* ..\backend\static\frontend\
# Linux/Mac:
cp -r dist/* ../backend/static/frontend/
```

#### 4. 运行项目

**开发模式：**

```bash
# 终端1：启动后端服务
cd backend
python manage.py runserver

# 终端2：启动前端开发服务器
cd frontend
npm run dev
```

**生产模式：**

```bash
# 只需启动后端服务，前端已构建到 static 目录
cd backend
python manage.py runserver
```

访问 `http://127.0.0.1:8000/` 即可查看应用。

## ⚙️ 配置说明

### 后端配置

主要配置文件：`backend/backend/settings.py`

- **静态文件配置**：
  - `STATIC_URL = 'static/'`
  - `STATICFILES_DIRS = [BASE_DIR / 'static']`

- **跨域配置**：
  - `CORS_ALLOWED_ORIGINS`：允许的前端域名
  - 默认允许 `http://localhost:5173`（Vite 开发服务器）

- **JWT 配置**：
  - Access Token 有效期：2 小时
  - Refresh Token 有效期：7 天

### 前端配置

主要配置文件：`frontend/vite.config.js`

- 开发服务器端口：5173
- 构建输出目录：`dist`

## 📡 API 接口

### 认证接口

- `POST /api/token/` - 获取 JWT Token
- `POST /api/token/refresh/` - 刷新 Token

### 页面路由

- `GET /` - 首页（返回前端应用）

## 🔧 开发说明

### 前端开发

前端使用 Vue3 + Vite 开发，支持热重载：

```bash
cd frontend
npm run dev
```

开发完成后需要构建并复制到后端 static 目录。

### 后端开发

后端使用 Django 开发，支持自动重载：

```bash
cd backend
python manage.py runserver
```

### 静态文件加载

项目使用 Django 的静态文件系统，模板中使用 `{% load static %}` 和 `{% static %}` 标签加载静态资源。

## 📝 注意事项

1. **开发环境**：当前配置为开发环境（`DEBUG = True`），生产环境需要修改相关配置
2. **数据库**：开发环境使用 SQLite，生产环境建议使用 PostgreSQL 或 MySQL
3. **静态文件**：生产环境建议使用 Nginx 等 Web 服务器处理静态文件
4. **密钥安全**：生产环境务必修改 `SECRET_KEY` 并妥善保管

## 📚 相关资源

- [Django 官方文档](https://docs.djangoproject.com/)
- [Vue 3 官方文档](https://cn.vuejs.org/)
- [LangChain 文档](https://python.langchain.com/)
- [Django REST Framework 文档](https://www.django-rest-framework.org/)

## 📄 许可证

本项目仅供学习交流使用。

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**注意**：本项目为课程项目，更多信息请参考课程页面。
