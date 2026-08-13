# AI 协作说明实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 在中英文 README 中加入对等、克制且可核查的 AI 协作与维护责任说明。

**架构：** 此变更仅涉及公开文档。在两份 README 的贡献说明之后、许可证之前各增加一个独立小节，不修改应用代码、配置、依赖或历史提交。

**技术栈：** Markdown、Git 提交共同作者尾注

## 全局约束

- 中文与英文声明必须语义对等。
- Codex 的范围限定为部分仓库分析、实现辅助、测试和文档工作。
- 项目维护者负责审核、验证、合并决定和后续维护。
- 不夸大 Codex 的自主性，不修改程序行为，不重写历史。
- 实现提交使用 `Co-authored-by: Codex <chatgpt-codex-connector[bot]@users.noreply.github.com>`。

---

### Task 1：增加中英双语 AI 协作说明

**文件：**

- 修改：`README.md`，在“贡献”之后增加“AI 协作说明”。
- 修改：`README_EN.md`，在“Contributing”之后增加“AI Collaboration Disclosure”。

**接口：**

- 输入：已确认的设计文档 `docs/superpowers/specs/2026-08-13-ai-collaboration-disclosure-design.md`
- 输出：两段语义对等的公开声明；不产生运行时接口或数据变更。

- [ ] **Step 1：记录修改前断言**

运行：

```powershell
git grep -n -E '^## (AI 协作说明|AI Collaboration Disclosure)$' -- README.md README_EN.md
```

预期：退出码为 `1`，表示两个小节尚不存在。

- [ ] **Step 2：写入最小文档改动**

在 `README.md` 的贡献说明之后写入：

```markdown
## AI 协作说明

OpenAI Codex 协助完成了本项目部分仓库分析、实现辅助、测试与文档工作。所有由 Codex 参与的变更均由项目维护者审核和验证；是否合并及后续维护责任由项目维护者承担。
```

在 `README_EN.md` 的贡献说明之后写入：

```markdown
## AI Collaboration Disclosure

OpenAI Codex assisted with parts of this project's repository analysis, implementation support, testing, and documentation. Every change involving Codex was reviewed and verified by the project maintainer, who remains responsible for merge decisions and ongoing maintenance.
```

- [ ] **Step 3：验证内容、格式和范围**

运行：

```powershell
git diff --check
git grep -n -E '^## (AI 协作说明|AI Collaboration Disclosure)$' -- README.md README_EN.md
git diff --name-only HEAD
```

预期：格式检查通过；两个标题各出现一次；相对 `HEAD` 仅有 `README.md` 与 `README_EN.md` 被修改。

- [ ] **Step 4：提交并确认共同作者**

运行：

```powershell
git add README.md README_EN.md
git commit -m "docs: disclose AI collaboration" -m "Co-authored-by: Codex <chatgpt-codex-connector[bot]@users.noreply.github.com>"
git show -s --format='%H%n%B' HEAD
```

预期：提交成功，提交正文包含准确的 Codex Bot 共同作者尾注。
