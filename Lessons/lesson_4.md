# Lesson 4：流式布局
> 本文对应课程「4. 流式布局」，含个人主页、首页、搜索、好友页面（前半部分）。

---

## 上节课的补丁

1. **创作按钮路由**：将导航栏中「创作」按钮的路由改为 **create-index**（对应 `/create/`、CreateIndex 页面）。
2. **删除角色时清理图片**：在 `AIFriends/backend/web/views/create/character/remove.py` 中，删除角色**之前**先删除其头像和背景图：
   - 使用 `Character.objects.get(pk=character_id, author__user=request.user)` 取出角色实例；
   - 调用 `remove_old_photo(character.photo)`、`remove_old_photo(character.background_image)`；
   - 再执行 `character.delete()`。  
   （注意：不要写成 `character = ...get().delete()`，否则得到的是删除结果而非模型实例，后续会报错。）

---

## 1. 实现个人主页

### 1.1 创建后端

在 `AIFriends/backend/web/views/create/character/` 下实现：

**get_list.py**：返回当前用户空间下的**角色列表**和**作者（用户）信息**。

- GET：`request.query_params` 取 `items_count`、`user_id`。
- 根据 `user_id` 找到对应用户及 `UserProfile`，再按 `author=user_profile` 筛选角色，按 `-id` 排序，分页切片 `[items_count: items_count + 20]`。
- 返回 `result: 'success'`、`user_profile`（含 `user_id, username, profile, photo`）、`characters`（列表，每项含 `id, name, profile, photo.url, background_image.url, author` 等）。

在 `AIFriends/backend/web/urls.py` 中添加路由：`path('api/create/character/get_list/', GetListCharacterView.as_view())`。

### 1.2 实现前端

**1.2.1 空组件**

- `AIFriends/frontend/src/views/user/space/components/UserInfoField.vue`：展示个人信息（头像、用户名、AIFriends 号、简介）。
- `AIFriends/frontend/src/components/character/Character.vue`：展示角色卡片（背景图、头像、名字、简介、作者信息；可选编辑/删除按钮）。

**1.2.2 个人主页对接**

在 `AIFriends/frontend/src/views/user/space/SpaceIndex.vue` 中：

- 调用 `get_list` 接口，维护 `userProfile`、`characters`、`hasCharacters`、`isLoading`。
- **网格布局**（随屏幕宽度自动每行数量、均匀排列、最后一行左对齐）：

```html
<div class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-9 mt-12 justify-items-center w-full px-9">
  ...
</div>
```

- **渐变遮罩**（卡片上从下黑到上透明）：`bg-linear-to-t from-black/40 to-transparent`。
- **流式加载**：使用哨兵元素 + `IntersectionObserver`，哨兵进入视口时请求下一页（`loadMore`），直到 `get_list` 返回空列表则设 `hasCharacters = false`。

流式加载示例：

```vue
<script setup>
const sentinelRef = useTemplateRef('sentinel-ref')
let observer = null

function checkSentinelVisible() {  // 判断哨兵是否能被看到
  if (!sentinelRef.value) return false
  const rect = sentinelRef.value.getBoundingClientRect()
  return rect.top < window.innerHeight && rect.bottom > 0
}

onMounted(async () => {
  await loadMore()

  observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) loadMore()
      })
    },
    { root: null, rootMargin: '2px', threshold: 0 }
  )
  observer.observe(sentinelRef.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
})
</script>

<template>
  ...
  <div ref="sentinel-ref" class="h-2 mt-8"></div>
  ...
</template>
```

- **修改角色**：卡片上编辑按钮跳转 `update-character`，params 带 `character_id`。
- **删除角色**：卡片上删除按钮调用 `POST /api/create/character/remove/`，body 传 `character_id`；成功后 `emit('remove', character.id)`，父组件从列表中移除该项。删除后可在 `backend/media/` 下确认对应头像、背景图是否被删除。

### 1.3 将前端代码打包到后端

删除调试信息后执行前端构建，将产物部署到后端静态/模板目录。

---

## 2. 实现首页

### 2.1 创建后端

在 `AIFriends/backend/web/views/homepage/` 下实现：

**index.py**：返回**所有角色**列表（分页）。

- GET：`request.query_params` 取 `items_count`（默认 0），切片 `[items_count: items_count + 20]`，按 `-id` 排序。
- 返回 `result: 'success'`、`characters`（结构可与 get_list 中单条角色一致，含 `author` 等）。

在 `urls.py` 中添加：`path('api/homepage/index/', HomepageIndexView.as_view())`。

### 2.2 实现前端

实现 `AIFriends/frontend/src/views/homepage/HomepageIndex.vue`：

- 与 SpaceIndex 类似：流式加载、哨兵、网格布局；请求 `GET /api/homepage/index/`，params 传 `items_count`。
- 首页不传 `user_id`，展示全部角色；个人主页传 `user_id`，展示该用户空间角色。

### 2.3 添加搜索功能

**2.3.1 导航栏搜索**

在 `AIFriends/frontend/src/components/navbar/NavBar.vue` 中：

- 点击搜索按钮后，跳转到**首页**，并把搜索文本放到 URL 的 **query 参数**（如 `q`）中。
- 监听 `route.query.q`，将最新值赋给搜索框的 `searchQuery`，这样**刷新页面后**搜索框能自动回填。

**2.3.2 首页带搜索请求**

在 `AIFriends/frontend/src/views/homepage/HomepageIndex.vue` 中：

- 请求时把搜索文本作为参数传给后端（如 `search_query: route.query.q || ''`）。
- **监听 `route.query.q` 变化**：变化时清空当前列表、重置 `hasCharacters`，再重新调用 `loadMore()`，从而根据新关键词重新拉取角色列表。

**2.3.3 后端支持搜索**

在 `AIFriends/backend/web/views/homepage/index.py` 中：

- 从 `request.query_params` 取 `search_query`（可选）。
- 若 `search_query` 非空，用 `Q(name__icontains=search_query) | Q(profile__icontains=search_query)` 过滤后再分页；否则使用全部角色。
- 分页仍为 `[items_count: items_count + 20]`。

### 2.4 将前端代码打包到后端

同 1.3。

---

## 3. 实现好友页面（本节上了一半）

### 3.1 创建后端

**3.1.1 创建数据库**

在 `AIFriends/backend/web/models/friend.py` 中创建 **Friend** 模型（例如：用户、角色、创建时间等；`character = models.ForeignKey(Character, on_delete=models.CASCADE)` 表示删除角色时会**级联删除**关联的 Friend）。

**3.1.2 创建 views**

在 `AIFriends/backend/web/views/friend/` 下实现：

- **get_or_create.py**：若已存在该好友则返回，否则创建并返回。
- **remove.py**：删除好友。
- **get_list.py**：获取好友列表。

**3.1.3 实现路由**

在 `AIFriends/backend/web/urls.py` 中为上述接口添加路由。

### 3.2 实现前端（本节上了一半）

**3.2.1 聊天相关组件**

在 `AIFriends/frontend/src/components/character/chat_field/` 下创建：

- **ChatField.vue**：显示聊天界面。
- **input_field/InputField.vue**：聊天输入框。
- **character_photo_field/CharacterPhotoField.vue**：虚拟角色头像。

将**模态框背景**设为聊天背景图（使用好友对应角色的 `background_image`）：

```js
const modalStyle = computed(() => {
  if (props.friend?.character) {
    return {
      backgroundImage: `url(${props.friend.character.background_image})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
    }
  }
  return {}
})
```

在 `AIFriends/frontend/src/components/character/Character.vue` 中：**点击角色卡片**时打开上述聊天界面（模态框）。

**3.2.2 好友列表页面**

- 实现 `AIFriends/frontend/src/views/friend/FriendIndex.vue`（展示好友列表、可删除好友）。
- 删除好友：调用后端 remove 接口，并从前端列表移除。
- **阻止卡片内点击事件冒泡**：在卡片内按钮或链接上使用 `@click.stop`，避免触发卡片的「打开聊天」等外层点击。
- 因 `Character` 删除时级联删除 `Friend`，删除角色后其关联好友记录也会被删除。

### 3.3 将前端代码打包到后端

（待课程后半部分完成后一并打包。）

---

## 小结

| 模块       | 后端 | 前端 |
|------------|------|------|
| 个人主页   | get_list（角色列表 + user_profile）、remove 前删头像/背景 | UserInfoField、Character、SpaceIndex、网格、流式加载、编辑/删除 |
| 首页       | homepage/index（全角色分页、search_query 过滤） | HomepageIndex、流式加载 |
| 搜索       | index 支持 search_query | NavBar 跳首页带 q、HomepageIndex 带 search_query、watch query 重载 |
| 好友（半） | Friend 模型、get_or_create/remove/get_list | ChatField、InputField、CharacterPhotoField、Character 点开聊天、FriendIndex、@click.stop |

当前课程进度：个人主页与首页、搜索已完成；好友页面的后端与聊天组件、好友列表已讲一半，后续会补全聊天逻辑与打包步骤。
