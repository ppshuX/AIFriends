# 路由懒加载实施计划

> **执行者要求：** 必须使用 `executing-plans` 按任务执行；步骤使用复选框跟踪。

**目标：** 在不改变路由、鉴权守卫和页面行为的前提下，将九个页面组件改为按路由加载，使入口 JavaScript 小于 Vite 的 500 kB 告警阈值。

**架构：** 保留 Vue Router、Pinia 和应用外壳的同步加载，只把路由表中的页面组件替换为 `() => import(...)`。Vite 负责生成页面级异步 chunk，现有 postbuild 继续同步 Django 模板中的入口资源哈希。

**技术栈：** Vue 3、Vue Router 4、Vite 7、Node.js 22+、Django 静态模板。

## 全局约束

- 不修改任何路由 path、name、meta、重定向或 `beforeEach` 守卫。
- 不新增加载界面、重试逻辑、预取规则、Service Worker 或 `manualChunks`。
- `backend/static/frontend/` 继续保持忽略，只提交路由文件和生成后的 Django 模板。
- 所有 npm 命令从规范 worktree 的 `frontend/` 目录执行，避免 Windows 双路径盘符导致 Vite 入口解析失败。
- 不推送、不合并、不部署。

---

### 任务 1：将页面组件改为路由级动态导入

**文件：**
- 修改：`frontend/src/router/index.js`
- 生成并修改：`backend/web/templates/index.html`

**接口：**
- 消费：Vue Router 路由记录的 `component` 字段。
- 产出：九个返回 Vue SFC 模块 Promise 的动态导入函数；现有路由接口保持不变。

- [ ] **步骤 1：运行静态导入契约检查并确认 RED**

从仓库根目录运行：

```powershell
@'
const fs = require('fs')
const source = fs.readFileSync('frontend/src/router/index.js', 'utf8')
const imports = [...source.matchAll(/^import\s+\w+\s+from\s+["']@\/views\//gm)]
if (imports.length) {
  console.error(`${imports.length} static route-view imports remain`)
  process.exit(1)
}
'@ | node -
```

预期：退出码 1，并输出 `9 static route-view imports remain`。

- [ ] **步骤 2：用动态导入替换九个页面静态导入**

删除 `HomepageIndex` 到 `UpdateCharacter` 的九条静态 import，只保留：

```js
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user.js'
```

将路由表替换为以下内容；文件中的 `beforeEach` 和 `export default router` 原样保留：

```js
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', component: () => import('@/views/homepage/HomepageIndex.vue'), name: 'homepage-index', meta: { needLogin: false } },
    { path: '/friend/', component: () => import('@/views/friend/FriendIndex.vue'), name: 'friend-index', meta: { needLogin: true } },
    { path: '/create/', component: () => import('@/views/create/CreateIndex.vue'), name: 'create-index', meta: { needLogin: true } },
    { path: '/create/character/update/:character_id/', component: () => import('@/views/create/character/UpdateCharacter.vue'), name: 'update-character', meta: { needLogin: true } },
    { path: '/login/', component: () => import('@/views/user/account/LoginIndex.vue'), name: 'user-account-login-index', meta: { needLogin: false } },
    { path: '/register/', component: () => import('@/views/user/account/RegisterIndex.vue'), name: 'user-account-register-index', meta: { needLogin: false } },
    { path: '/user/space/:user_id/', component: () => import('@/views/user/space/SpaceIndex.vue'), name: 'user-space-index', meta: { needLogin: true } },
    { path: '/user/profile/', component: () => import('@/views/user/profile/ProfileIndex.vue'), name: 'user-profile-index', meta: { needLogin: true } },
    { path: '/:pathMatch(.*)*', component: () => import('@/views/error/NotFoundIndex.vue'), name: 'not-found' },
  ],
})
```

- [ ] **步骤 3：重跑静态导入契约并确认 GREEN**

运行步骤 1 的命令。

预期：退出码 0，无静态页面 import。

- [ ] **步骤 4：运行生产构建**

从规范路径的 `frontend/` 目录运行：

```powershell
npm run build
```

预期：构建成功，输出多个 `.js` chunk；postbuild 成功更新 `backend/web/templates/index.html`。

- [ ] **步骤 5：验证入口包大小和分块数量**

从仓库根目录运行：

```powershell
$assetRoot = Resolve-Path 'backend/static/frontend/assets'
$builtIndex = Get-Content -Raw 'backend/static/frontend/index.html'
$entryMatch = [regex]::Match($builtIndex, 'src="/assets/([^"]+\.js)"')
if (-not $entryMatch.Success) { throw 'Unable to locate Vite entry script' }
$entryPath = Join-Path $assetRoot $entryMatch.Groups[1].Value
$entryBytes = (Get-Item $entryPath).Length
$chunkCount = (Get-ChildItem $assetRoot -Filter '*.js').Count
if ($entryBytes -ge 500000) { throw "Entry chunk remains too large: $entryBytes bytes" }
if ($chunkCount -le 1) { throw "Expected route chunks, found $chunkCount JavaScript file" }
"Entry: $entryBytes bytes; JavaScript chunks: $chunkCount"
```

预期：入口小于 500000 bytes，JavaScript 文件数大于 1。

- [ ] **步骤 6：运行安全与后端回归检查**

```powershell
cd frontend
npm audit --audit-level=moderate --registry=https://registry.npmjs.org
cd ..\backend
$env:DJANGO_SECRET_KEY='django-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
$env:JWT_SIGNING_KEY='jwt-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
python manage.py test -v 2
python manage.py check
```

预期：npm 为 0 vulnerabilities；Django 发现 11 个测试且全部通过；系统检查无问题。

- [ ] **步骤 7：检查提交边界并提交**

```powershell
git diff --check
git status --short
git diff -- frontend/src/router/index.js backend/web/templates/index.html
git add frontend/src/router/index.js backend/web/templates/index.html
git commit -m "perf: lazy-load route views"
```

预期：仅两份批准文件进入 commit。
