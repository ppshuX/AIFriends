# 贡献指南

感谢你愿意参与 AIFriends。为了让改动容易验证、评审和回退，请尽量保持每个
Pull Request 目标明确，并沿用现有的 Django + Vue 架构与代码风格。

## 开始之前

- 功能改动较大时，建议先创建 Issue 说明问题、目标和预期行为。
- Bug 修复请尽量提供复现步骤；界面改动请附截图或录屏。
- 不要提交 `.env`、API Key、访问令牌、用户数据或其他敏感信息。
- 避免把无关格式化、大规模重构和功能改动混在同一个 Pull Request 中。

## 本地环境

后端需要 Python 3.12+，前端需要 Node.js 20.19+ 或 22.12+。完整安装步骤和
环境变量说明见 [README](README.md#-快速开始)。

依赖清单以 `backend/requirements.txt` 和 `frontend/package-lock.json` 为准。
根目录的 `requirements.txt` 只是后端清单的兼容入口。

## 提交前验证

后端命令必须在 `backend/` 目录执行，否则 Django 可能无法发现全部测试：

```bash
cd backend
python manage.py test -v 2
python manage.py check
python manage.py makemigrations --check --dry-run
```

前端使用锁文件安装并完成生产构建：

```bash
cd frontend
npm ci
npm run build
```

`npm run build` 会在忽略的 `backend/static/frontend/` 中生成构建产物，并通过
postbuild 更新受版本控制的 `backend/web/templates/index.html`。如果模板发生
变化，请确认它与本次前端改动有关并一并提交。

## 测试与改动原则

- Bug 修复先添加能稳定复现问题的测试，再实现最小修复。
- 新功能至少覆盖关键成功路径和失败路径。
- 不要通过删除断言、跳过测试或隐藏警告来让检查通过。
- 数据库模型变更必须提交对应迁移，并通过迁移漂移检查。
- AI、语音或第三方服务调用不得在自动化测试中依赖真实凭据或产生费用。

## Commit 与 Pull Request

- 一个 commit 只表达一个可独立理解的改动，避免为了数量拆分无意义提交。
- Commit 标题简洁说明意图，例如 `fix: ...`、`security: ...`、`docs: ...`。
- Pull Request 说明应包含修改原因、主要变化、验证命令和仍待处理的限制。
- CI 失败时，请先查看 Backend 或 Frontend job 的具体日志，再更新改动。
