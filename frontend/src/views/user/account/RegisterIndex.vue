<script setup>
import { ref } from "vue";
import { useUserStore } from "@/stores/user.js";
import { useRouter } from "vue-router";
import api from "@/js/http/api.js";

const username = ref("");
const password = ref("");
const passwordConfirm = ref("");
const errorMessage = ref("");

const user = useUserStore();
const router = useRouter();

async function handleRegister() {
  errorMessage.value = "";

  if (!username.value.trim()) {
    errorMessage.value = "用户名不能为空";
  } else if (!password.value.trim()) {
    errorMessage.value = "密码不能为空";
  } else if (!passwordConfirm.value.trim()) {
    errorMessage.value = "确认密码不能为空";
  } else if (password.value !== passwordConfirm.value) {
    errorMessage.value = "两次密码不一致";
  } else if (password.value.length < 6) {
    errorMessage.value = "密码长度不能少于6位";
  } else {
    try {
      const res = await api.post("/api/user/account/register/", {
        username: username.value,
        password: password.value,
        password_confirm: passwordConfirm.value,
      });
      const data = res.data;

      if (data.result === "success") {
        user.setAccessToken(data.access);
        user.setUserInfo(data);
        await router.push({
          name: "homepage-index",
        });
      } else {
        errorMessage.value = data.result || "注册失败，请稍后重试";
      }
    } catch (error) {
      console.log(error);
      errorMessage.value = "网络异常，请稍后重试";
    }
  }
}
</script>

<template>
  <div class="register-page flex justify-center py-8">
    <form
      @submit.prevent="handleRegister"
      class="fieldset bg-base-200 border-base-300 rounded-box w-xs border p-4"
    >
      <legend class="fieldset-legend">注册</legend>

      <label class="label">用户名</label>
      <input
        v-model="username"
        type="text"
        class="input input-bordered w-full"
        placeholder="输入用户名"
      />

      <label class="label">密码</label>
      <input
        v-model="password"
        type="password"
        class="input input-bordered w-full"
        placeholder="输入密码"
      />

      <label class="label">确认密码</label>
      <input
        v-model="passwordConfirm"
        type="password"
        class="input input-bordered w-full"
        placeholder="输入确认密码"
      />

      <p v-if="errorMessage" class="text-sm text-red-500 mt-1">
        {{ errorMessage }}
      </p>

      <button class="btn btn-neutral mt-4 w-full">注册</button>
      <div class="flex justify-end mt-2">
        <RouterLink
          :to="{ name: 'user-account-login-index' }"
          class="btn btn-sm btn-ghost text-base-content/70"
        >
          登录
        </RouterLink>
      </div>
    </form>
  </div>
</template>

<style scoped>
.register-page {
}
</style>
