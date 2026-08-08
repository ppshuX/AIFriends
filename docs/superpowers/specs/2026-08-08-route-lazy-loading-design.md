# Route Lazy Loading Design

## Goal

Reduce the frontend's initial JavaScript payload without changing routes, authentication
guards, page behavior, or the existing Vue/Django deployment flow.

The verified baseline build produces one primary JavaScript bundle of approximately
650.54 kB before gzip and reports Vite's 500 kB chunk warning. All nine route views are
currently imported synchronously by `frontend/src/router/index.js`.

## Scope

This change will:

- Replace the nine static route-view imports with Vue Router dynamic imports.
- Preserve every route path, name, meta field, component, and navigation guard.
- Rebuild the frontend and commit the generated Django template hash when it changes.
- Measure the new entry chunk and confirm that route-specific chunks are emitted.

This change will not:

- Add custom loading screens, prefetch rules, retry UI, or service workers.
- Change application state, authentication behavior, API requests, or page components.
- Add a manual Rollup chunk configuration.
- Attempt to remove the existing CSS optimizer warning.

## Chosen Approach

Use a dynamic import function directly in each route definition:

```js
{
  path: '/friend/',
  component: () => import('@/views/friend/FriendIndex.vue'),
  // Existing name and meta remain unchanged.
}
```

This uses Vue Router and Vite's native route-level code splitting. It keeps the router,
Pinia store, application shell, and navigation guard in the entry bundle while deferring
page implementation code until navigation reaches that page.

## Alternatives Considered

### Lazy-load only protected or heavy pages

This would reduce risk slightly but leave public pages in the entry bundle and require an
arbitrary distinction between eager and lazy routes. The router already provides a clean
boundary for every page, so partial adoption offers less value without a material safety
benefit.

### Configure `manualChunks`

Manual chunks can improve caching but do not necessarily reduce first-load execution, and
they couple the build configuration to dependency internals. It is unnecessary while the
more direct route boundary is unused.

## Runtime and Error Behavior

Navigation continues through the existing `beforeEach` guard. Once permitted, Vue Router
loads the selected view chunk and renders it normally. A network failure while fetching a
chunk will continue to use Vue Router's default rejected-navigation behavior; custom retry
or offline UI is a separate feature.

## Verification

1. Record the current route table so paths, names, meta fields, and components can be
   compared after editing.
2. Run `npm run build` from the canonical worktree path.
3. Confirm the build succeeds and emits multiple JavaScript chunks.
4. Confirm the entry JavaScript chunk is below Vite's 500 kB warning threshold.
5. Confirm postbuild updates only the expected static asset reference in
   `backend/web/templates/index.html`.
6. Run `npm audit` and the existing backend checks to ensure no unrelated regression.

## Commit Boundary

The implementation is suitable for one commit containing the router import change and the
generated Django template update. Generated files under `backend/static/frontend/` remain
ignored.
