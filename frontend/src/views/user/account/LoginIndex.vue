<script setup>
</script>

<template>
  <div class="login-page flex justify-center py-8">
    <fieldset class="fieldset bg-base-200 border-base-300 rounded-box w-xs border p-4">
      <legend class="fieldset-legend">登录</legend>

      <label class="label">用户名</label>
      <input type="text" class="input input-bordered w-full" placeholder="输入用户名" />

      <label class="label">密码</label>
      <input type="password" class="input input-bordered w-full" placeholder="输入密码" />

      <button class="btn btn-neutral mt-4 w-full">登录</button>
      <div class="flex justify-end mt-2">
        <RouterLink :to="{ name: 'register-index' }" class="btn btn-sm btn-ghost text-base-content/70">
          注册
        </RouterLink>
      </div>
    </fieldset>
  </div>
</template>

<style scoped>
.login-page {
}
</style>
