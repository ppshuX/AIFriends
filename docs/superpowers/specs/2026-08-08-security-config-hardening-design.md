# AIFriends 安全配置加固设计

## 背景

仓库当前公开提交了 Django `SECRET_KEY`，并让 SimpleJWT 默认复用该密钥签名访问令牌。`DEBUG`、允许的主机、CORS 来源和 refresh cookie 的 `secure` 属性也直接写在代码中。旧服务器已经过期，下一次上线可以重新生成全部密钥，因此无需兼容现有签名或会话。

## 目标

- 删除仓库内可用于运行服务的 Django 和 JWT 签名密钥。
- 让本地与生产环境都必须显式提供独立密钥。
- 缺失、过短或仍为示例占位值的密钥必须让 Django 拒绝启动。
- 将调试模式、允许的主机和 CORS 来源改为环境配置。
- 统一登录、注册、刷新和退出接口的 refresh cookie 行为。
- 为配置解析和 cookie 行为建立自动化回归测试。
- 更新公开文档，使新贡献者能按明确步骤生成安全的本地配置。

## 非目标

- 本任务不恢复或部署线上服务器，不生成线上真实密钥，不 push 分支。
- 本任务不调整 AI 模型、ASR、TTS、LanceDB 或其环境变量。
- 本任务不批量升级 Python 或前端依赖。
- 本任务不改变 JWT 有效期、认证接口路径或前端登录流程。
- 本任务不引入新的配置框架，也不拆分 Django settings 模块。

## 方案选择

采用单一 `settings.py` 与严格环境变量方案。相比拆分开发/生产 settings，它对现有结构改动更小；相比首次启动自动生成密钥，它在容器、多人开发和重新部署时更加可预测。

## 配置设计

新增 `backend/backend/env.py`，集中提供以下接口：

- `get_bool(name, default=False)`：接受 `true/false`、`1/0`、`yes/no`、`on/off`，其他非空值抛出 `ImproperlyConfigured`。
- `get_csv(name, default=())`：按逗号拆分、去除空白并丢弃空项。
- `get_required_secret(name)`：要求变量存在、长度至少为 50 个字符，且不等于示例占位值；错误信息只包含变量名，不回显密钥。

`backend/backend/settings.py` 在计算 `BASE_DIR` 后显式加载 `backend/.env`，然后读取：

- `DJANGO_SECRET_KEY`：必填，用作 Django `SECRET_KEY`。
- `JWT_SIGNING_KEY`：必填，显式写入 `SIMPLE_JWT["SIGNING_KEY"]`，不得与 Django 密钥相同。
- `DJANGO_DEBUG`：可选，默认 `false`。
- `DJANGO_ALLOWED_HOSTS`：可选，默认仅 `127.0.0.1,localhost`。
- `DJANGO_CORS_ALLOWED_ORIGINS`：可选；开发示例包含 Vite 的两个本地来源，生产可以留空以采用同源部署。

如果两个密钥相同，启动同样抛出 `ImproperlyConfigured`。代码中不保留开发密钥 fallback，避免已知默认值被误部署。

## Cookie 设计

新增 `backend/web/views/user/account/cookies.py`，提供：

- `set_refresh_token_cookie(response, token)`
- `delete_refresh_token_cookie(response)`

登录、注册和刷新接口统一调用设置函数，退出接口调用删除函数。Cookie 保持 `httponly=True`、`samesite="Lax"`、7 天有效期；`secure` 在 `DEBUG=False` 时为 `True`，在显式本地调试模式下为 `False`。设置和删除使用相同的 cookie 名称、路径与 SameSite 属性。

## 错误处理

配置错误在 Django 导入 settings 时立即失败，并指出需要修正的环境变量。错误信息不得包含变量值。AI 服务密钥仍可缺失，使贡献者可以先运行不涉及 AI 的页面；相关能力的启动检查留给后续任务。

## 测试设计

测试按 TDD 编写，并覆盖：

1. 缺失、过短和占位密钥被拒绝。
2. 两个签名密钥相同被拒绝。
3. 合法布尔值和 CSV 列表被正确解析，非法布尔值被拒绝。
4. Django settings 显式使用独立 JWT 签名密钥。
5. `DEBUG=True` 时 refresh cookie 不带 Secure，`DEBUG=False` 时带 Secure。
6. 删除 cookie 与设置 cookie 使用一致的名称和路径。

单元测试使用 Python 标准库和 Django 测试工具，不引入新的测试框架。完成后运行完整 Django 测试、`manage.py check`、`manage.py check --deploy`（记录预期的部署提醒）以及 Python 语法检查。

## 文档与迁移

新增 `backend/.env.example`，其中密钥使用不可运行的占位值，并提供基于 Python `secrets.token_urlsafe(64)` 的生成命令。README 将：

- 把最低 Python 版本改为 3.12。
- 使用 `pip install -r requirements.txt` 安装后端依赖。
- 说明复制 `.env.example`、生成两个不同密钥和设置本地调试参数的步骤。
- 明确 `.env` 不得提交，生产部署必须重新生成密钥并保持 `DJANGO_DEBUG=false`。

旧服务器及旧令牌无需迁移。新服务器上线前生成全新密钥即可，任何由旧公开密钥签发的令牌都不会在新环境中继续有效。

## 验收标准

- 受版本控制文件中不再存在可运行的 Django 或 JWT 默认密钥。
- 未配置安全密钥时，后端以可理解且不泄密的错误拒绝启动。
- 本地开发按 README 配置后可以运行，生产配置默认关闭 DEBUG 并使用 Secure refresh cookie。
- 设置解析和 cookie 行为有自动化回归测试。
- 所有验证结果基于实际命令输出记录，工作区只包含本任务相关改动。
