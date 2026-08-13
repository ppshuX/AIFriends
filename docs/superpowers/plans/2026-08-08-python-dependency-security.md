# Python 依赖安全修复实施计划

> **执行者要求：** 必须使用 `executing-plans` 按任务执行；步骤使用复选框跟踪。

**目标：** 将 `pip-audit` 当前报告的 20 个漏洞包修复到兼容版本，并把 Python 与 npm 审计加入 CI。

**架构：** 先独立升级 Django、网络和图像基础包，再联合升级 LangChain/LangGraph 生态。每一阶段都在仓库外的新虚拟环境中完成全量安装、`pip check`、审计和项目回归，AI 阶段只做凭据隔离的导入与本地图构建，不调用远程服务。

**技术栈：** Python 3.12、pip 26、pip-audit 2.10.1、Django 6、LangChain 1、LangGraph 1、GitHub Actions。

## 全局约束

- `backend/requirements.txt` 是唯一依赖源，根目录 `requirements.txt` 继续只做转发。
- 所有版本保持现有主版本；解析策略使用 pip 默认 `only-if-needed`，不使用 `--upgrade-strategy eager`。
- 不调用 OpenAI 兼容 API、语音服务、远程 LanceDB 或其他付费服务。
- 若 AI 升级需要主版本迁移或现有接口适配，先停止该任务并重新审查设计。
- 不创建仓库内虚拟环境，不提交缓存、审计输出或凭据。
- 每个阶段独立提交；不推送、不合并、不部署、不操作生产数据库。

---

### 任务 1：升级 Web 与运行时基础依赖

**文件：**
- 修改：`backend/requirements.txt`

**接口：**
- 消费：Python 3.12 与现有后端源码。
- 产出：可完整安装且基础漏洞包清零的精确版本集合。

- [ ] **步骤 1：记录基础漏洞 RED**

```powershell
$auditPython = 'C:\Users\Lenovo\AppData\Local\Codex\venvs\AIFriends-security-config\Scripts\python.exe'
& $auditPython -m pip_audit -r backend/requirements.txt
```

预期：退出码 1；输出至少包含 `aiohttp 3.13.3`、`django 6.0.1`、`pillow 12.1.0` 和 `pyjwt 2.10.1`。

- [ ] **步骤 2：精确更新十一项基础版本**

在 `backend/requirements.txt` 中只做以下替换：

```text
aiohttp==3.13.3          -> aiohttp==3.14.3
click==8.3.1             -> click==8.3.3
Django==6.0.1            -> Django==6.0.7
idna==3.11               -> idna==3.15
pillow==12.1.0           -> pillow==12.3.0
pydantic-settings==2.13.1 -> pydantic-settings==2.14.2
Pygments==2.19.2         -> Pygments==2.20.0
PyJWT==2.10.1            -> PyJWT==2.13.0
python-dotenv==1.2.1     -> python-dotenv==1.2.2
requests==2.32.5         -> requests==2.33.0
urllib3==2.6.3           -> urllib3==2.7.0
```

- [ ] **步骤 3：从零安装更新后的完整依赖**

```powershell
$runtimeSecurityVenv = Join-Path $env:LOCALAPPDATA 'Codex\venvs\AIFriends-python-runtime-security'
python -m venv $runtimeSecurityVenv
& "$runtimeSecurityVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$runtimeSecurityVenv\Scripts\python.exe" -m pip install -r backend/requirements.txt
& "$runtimeSecurityVenv\Scripts\python.exe" -m pip check
```

预期：安装与 `pip check` 均退出 0，输出 `No broken requirements found.`。

- [ ] **步骤 4：运行后端回归**

从 `backend/` 目录运行：

```powershell
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
$env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
& "$runtimeSecurityVenv\Scripts\python.exe" manage.py test -v 2
& "$runtimeSecurityVenv\Scripts\python.exe" manage.py check
& "$runtimeSecurityVenv\Scripts\python.exe" manage.py makemigrations --check --dry-run
```

预期：发现 11 个测试且全部通过；系统检查无问题；无迁移变化。

- [ ] **步骤 5：确认只剩 AI 生态漏洞**

从仓库根目录运行：

```powershell
@'
import json
import subprocess

python = r'C:\Users\Lenovo\AppData\Local\Codex\venvs\AIFriends-security-config\Scripts\python.exe'
result = subprocess.run(
    [python, '-m', 'pip_audit', '-r', 'backend/requirements.txt', '-f', 'json'],
    capture_output=True, text=True, check=False,
)
data = json.loads(result.stdout)
actual = {
    item['name'] for item in data['dependencies'] if item.get('vulns')
}
expected = {
    'langchain', 'langchain-classic', 'langchain-core',
    'langchain-openai', 'langchain-text-splitters', 'langgraph',
    'langgraph-checkpoint', 'langgraph-sdk', 'langsmith',
}
if actual != expected:
    raise SystemExit(f'Unexpected vulnerable package set: {sorted(actual)}')
print('Only the approved AI dependency group remains vulnerable')
'@ | python -
```

预期：退出 0，并输出只剩批准的 AI 依赖组。

- [ ] **步骤 6：提交基础依赖修复**

```powershell
git diff --check
git add backend/requirements.txt
git commit -m "security: update backend runtime dependencies"
```

---

### 任务 2：联合升级 LangChain 与 LangGraph 生态

**文件：**
- 创建：`backend/backend/tests/test_ai_integrations.py`
- 修改：`backend/requirements.txt`

**接口：**
- 消费：`ChatGraph.create_app()`、`MemoryGraph.create_app()` 与 AI 集成模块 import。
- 产出：兼容且审计为零的 AI 依赖集合；两个无需网络即可编译的本地图对象。

- [ ] **步骤 1：添加凭据隔离的 AI smoke tests**

创建 `backend/backend/tests/test_ai_integrations.py`：

```python
import importlib
import os
from unittest.mock import patch

from django.test import SimpleTestCase


AI_MODULES = (
    "web.documents.utils.custom_embeddings",
    "web.documents.utils.insert_documents",
    "web.views.friend.message.chat.chat",
    "web.views.friend.message.chat.graph",
    "web.views.friend.message.memory.graph",
    "web.views.create.character.voice.custom.create_voice",
    "web.views.create.character.voice.custom.delete_voice",
    "web.views.create.character.voice.custom.list_voice",
)


class AIIntegrationSmokeTests(SimpleTestCase):
    def test_ai_integration_modules_import_without_remote_calls(self):
        for module_name in AI_MODULES:
            with self.subTest(module=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))

    def test_chat_and_memory_graphs_compile_without_remote_calls(self):
        with patch.dict(
            os.environ,
            {"API_KEY": "test-only-key", "API_BASE": "http://127.0.0.1:9/v1"},
            clear=False,
        ):
            from web.views.friend.message.chat.graph import ChatGraph
            from web.views.friend.message.memory.graph import MemoryGraph

            self.assertIsNotNone(ChatGraph.create_app())
            self.assertIsNotNone(MemoryGraph.create_app())
```

- [ ] **步骤 2：在升级前运行 smoke tests**

从 `backend/` 目录运行：

```powershell
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
$env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
& "$runtimeSecurityVenv\Scripts\python.exe" manage.py test backend.tests.test_ai_integrations -v 2
```

预期：2 个测试通过，证明测试本身不会发起远程调用。

- [ ] **步骤 3：更新 AI 生态的精确兼容版本**

在 `backend/requirements.txt` 中应用以下最终解析结果：

```text
langchain==1.2.10              -> langchain==1.3.9
langchain-classic==1.0.1       -> langchain-classic==1.0.7
langchain-core==1.2.16         -> langchain-core==1.5.3
langchain-openai==1.1.10       -> langchain-openai==1.1.14
新增                              langchain-protocol==0.0.18
langchain-text-splitters==1.1.1 -> langchain-text-splitters==1.1.2
langgraph==1.0.9               -> langgraph==1.2.10
langgraph-checkpoint==4.0.0    -> langgraph-checkpoint==4.1.1
langgraph-prebuilt==1.0.8      -> langgraph-prebuilt==1.1.0
langgraph-sdk==0.3.9           -> langgraph-sdk==0.4.2
langsmith==0.7.7               -> langsmith==0.8.18
openai==2.24.0                 -> openai==2.53.0
websockets==16.0               -> websockets==15.0.1
```

保留 `langchain-community==0.4.1`，因为它满足新 `langchain-core` 的约束且审计无漏洞。

- [ ] **步骤 4：从零安装 AI 安全集合**

```powershell
$aiSecurityVenv = Join-Path $env:LOCALAPPDATA 'Codex\venvs\AIFriends-python-ai-security'
python -m venv $aiSecurityVenv
& "$aiSecurityVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$aiSecurityVenv\Scripts\python.exe" -m pip install -r backend/requirements.txt
& "$aiSecurityVenv\Scripts\python.exe" -m pip check
```

预期：完整安装成功，`pip check` 输出 `No broken requirements found.`。

- [ ] **步骤 5：运行 AI smoke tests 与完整后端回归**

从 `backend/` 目录运行：

```powershell
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
$env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
& "$aiSecurityVenv\Scripts\python.exe" manage.py test backend.tests.test_ai_integrations -v 2
& "$aiSecurityVenv\Scripts\python.exe" manage.py test -v 2
& "$aiSecurityVenv\Scripts\python.exe" manage.py check
& "$aiSecurityVenv\Scripts\python.exe" manage.py makemigrations --check --dry-run
```

预期：AI smoke tests 2/2 通过；完整测试总数 13 且全部通过；系统检查无问题；无迁移变化。

若升级后 smoke test 失败，不修改测试绕过失败；停止本步骤，使用 `systematic-debugging` 定位确切 API 变化，再为该变化增加最小失败断言。

- [ ] **步骤 6：确认 Python 审计清零**

```powershell
& $auditPython -m pip_audit -r backend/requirements.txt
```

预期：退出 0，输出 `No known vulnerabilities found`。

- [ ] **步骤 7：运行语法和差异检查并提交**

```powershell
@'
import ast
from pathlib import Path
for path in Path('backend').rglob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
print('Python syntax OK')
'@ | & "$aiSecurityVenv\Scripts\python.exe" -
git diff --check
git add backend/requirements.txt backend/backend/tests/test_ai_integrations.py
git commit -m "security: update AI framework dependencies"
```

---

### 任务 3：在 CI 中持续审计依赖

**文件：**
- 修改：`.github/workflows/ci.yml`

**接口：**
- 消费：`backend/requirements.txt`、`frontend/package-lock.json`。
- 产出：Backend job 的 `pip check`/`pip-audit` 门禁和 Frontend job 的 `npm audit` 门禁。

- [ ] **步骤 1：运行 CI 审计契约并确认 RED**

```powershell
$workflow = Get-Content -Raw '.github/workflows/ci.yml'
foreach($required in @('pip check','pip_audit','npm audit')) {
    if(-not $workflow.Contains($required)) { throw "Missing CI audit command: $required" }
}
```

预期：退出码 1，至少报告缺少 `pip check`。

- [ ] **步骤 2：在 Backend job 中增加 Python 审计**

在 `Install backend dependencies` 后增加：

```yaml
      - name: Install dependency auditor
        run: python -m pip install pip-audit==2.10.1

      - name: Audit backend dependencies
        working-directory: backend
        run: |
          python -m pip check
          python -m pip_audit -r requirements.txt
```

- [ ] **步骤 3：在 Frontend job 中增加 npm 审计**

在 `Install frontend dependencies` 后增加：

```yaml
      - name: Audit frontend dependencies
        working-directory: frontend
        run: npm audit --audit-level=moderate
```

- [ ] **步骤 4：验证工作流结构和审计命令**

重跑步骤 1，预期退出 0。然后运行：

```powershell
@'
from pathlib import Path
import yaml
path = Path('.github/workflows/ci.yml')
data = yaml.load(path.read_text(encoding='utf-8'), Loader=yaml.BaseLoader)
assert set(data['jobs']) == {'backend', 'frontend'}
assert data['permissions']['contents'] == 'read'
print('Workflow structure OK')
'@ | & $auditPython -
```

预期：YAML 解析成功，仍只有 Backend 和 Frontend 两个 job，权限保持只读。

- [ ] **步骤 5：本地运行等价审计与回归**

```powershell
& $auditPython -m pip_audit -r backend/requirements.txt
cd frontend
npm audit --audit-level=moderate --registry=https://registry.npmjs.org
npm run build
cd ..\backend
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
$env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
& "$aiSecurityVenv\Scripts\python.exe" manage.py test -v 2
```

预期：两类审计均为零；前端构建成功；后端 13 个测试全部通过。

- [ ] **步骤 6：提交 CI 门禁**

```powershell
git diff --check
git add .github/workflows/ci.yml
git commit -m "ci: audit project dependencies"
```
