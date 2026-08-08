# Python Dependency Security Remediation Design

## Goal

Remediate the Python dependency vulnerabilities reported by `pip-audit` while keeping
framework and AI ecosystem upgrades independently reviewable and avoiding paid or remote
model calls during validation.

The verified baseline reports 129 advisory records across 20 pinned packages. The findings
fall into two materially different compatibility groups: common web/runtime libraries and
the tightly coupled LangChain/LangGraph ecosystem.

## Scope and Order

### Phase 1: Web and runtime foundations

Update the non-AI vulnerable packages to audited fixed releases:

- `aiohttp`
- `click`
- `Django`
- `idna`
- `urllib3`
- `requests`
- `pydantic-settings`
- `Pillow`
- `Pygments`
- `PyJWT`
- `python-dotenv`

The first phase must leave the project installable, pass `pip check`, preserve all Django
tests and checks, and remove findings for these packages. Remaining audit findings must be
limited to the AI dependency group before this phase is committed.

### Phase 2: LangChain and LangGraph ecosystem

Resolve a compatible, audited set for:

- `langchain`
- `langchain-core`
- `langchain-classic`
- `langchain-openai`
- `langchain-text-splitters`
- `langgraph`
- `langgraph-checkpoint`
- `langgraph-sdk`
- `langsmith`

Because these packages constrain one another, versions will be resolved together in a
clean external virtual environment. The repository will retain exact pins after resolution.
The phase must not be committed if imports, graph construction, or the audit fail.

## Dependency Source of Truth

`backend/requirements.txt` remains the canonical pinned dependency list. The root
`requirements.txt` continues to delegate to it. Adopting Poetry, uv, pip-tools, or a new
packaging layout is out of scope for this remediation.

All dependency resolution occurs in task-specific virtual environments outside the
repository. No virtual environment, cache, audit report, or credential file is committed.

## Compatibility Strategy

For Phase 1, use the newest fixed patch/minor versions reported by the current audit within
the existing major version wherever possible. Install the complete pinned requirements
from scratch so resolver conflicts cannot be hidden by an already-populated environment.

For Phase 2, start with the current major lines and allow only the minimum set of compatible
minor/patch updates required to clear advisories. If the resolver requires a major upgrade
or application API changes, stop that phase and revise the design before modifying AI code.

## Credential-Free Verification

Neither phase may call OpenAI-compatible APIs, speech services, vector databases hosted on
remote infrastructure, or any paid external service.

Verification will include:

1. Clean installation from `backend/requirements.txt`.
2. `python -m pip check`.
3. `python -m pip_audit -r backend/requirements.txt`.
4. All discovered Django tests, with the expected count recorded.
5. `manage.py check` and `makemigrations --check --dry-run`.
6. Python syntax parsing for the backend tree.
7. Credential-free import smoke tests for the chat, memory, document, and voice integration
   modules that use the upgraded libraries.
8. Construction of local LangChain/LangGraph objects only where doing so cannot trigger a
   network request.

If a smoke test exposes an application incompatibility, add a focused failing test before
making the smallest code adaptation. Such adaptations belong in the AI dependency phase,
not the foundational package commit.

## Commit Boundaries

- Commit 1: web/runtime dependency pins only.
- Commit 2: compatible AI ecosystem pins plus any narrowly required, tested API adaptation.
- Commit 3 only if needed: CI audit automation after the repository reaches zero known
  vulnerabilities. It must not be added while the audit is expected to fail.

Each commit is verified independently. No deployment, production database operation,
remote AI request, merge, or push is part of this work.
