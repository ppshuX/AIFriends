<script setup>
import NavBar from "@/components/navbar/NavBar.vue";
import { onMounted } from "vue";
import { useUserStore } from "@/stores/user.js";
import { useRoute, useRouter } from "vue-router";
import api from "@/js/http/api.js";

const user = useUserStore();
const route = useRoute();
const router = useRouter();

onMounted(async () => {
  try {
    // 修正 URL：使用后端实际路径 /api/user/account/get_user_info/
    const res = await api.get("/api/user/account/get_user_info/");
    const data = res.data;
    if (data.result === "success") {
      user.setUserInfo(data);
    }
  } catch (error) {
    console.error(error);
  } finally {
    // 按你原先的设计，标记已经尝试拉取过用户信息
    user.setHasPulledUserInfo(true);

    // 如果当前路由需要登录但用户未登录，则跳转到登录页
    if (route.meta.needLogin && !user.isLogin()) {
      await router.replace({
        name: "user-account-login-index",
      });
    }
  }
});
</script>

<template>
  <NavBar>
    <RouterView />
  </NavBar>
</template>

<style scoped>
</style>
