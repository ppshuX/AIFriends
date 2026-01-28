<script setup>
import useUserMenu from "./useUserMenu";
import UserSpaceIcon from "@/components/navbar/icons/UserSpaceIcon.vue";
import UserProfileIcon from "@/components/navbar/icons/UserProfileIcon.vue";
import UserLogoutIcon from "@/components/navbar/icons/UserLogoutIcon.vue";

const user = useUserMenu();

function closeMenu() {
  const element = document.activeElement
  if (element && element instanceof HTMLElement) element.blur()
}
</script>

<template>
<div class="dropdown dropdown-end">
  <div tabindex="0" role="button" class="avatar btn btn-circle w-8 h-8 mr-6">
    <div class="w-8 rounded-full">
      <img :src="user.photo" alt="">
    </div>
  </div>
  <ul tabindex="-1" class="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm">
    <li>
      <RouterLink @click="closeMenu" :to="{name: 'user-space-index', params: {user_id: user.id}}">
        <div class="avater">
          <div class="w-10 rounded-full">
            <img src="use.photo" alt="">
          </div>
        </div>
        <span class="text-base font-bold line-clamp-1">{{ user.username }}</span>
      </RouterLink>
    </li>
    <li>
      <RouterLink @click="closeMenu" :to="{name: 'user-space-index', params: {user_id: user.id}}" class="text-sm font-bold py-3">
        <UserSpaceIcon />
        个人空间
      </RouterLink>
    </li>
    <li>
      <RouterLink @click="closeMenu" :to="{ name: 'profile-index' }" class="text-sm font-bold py-3">
        <UserProfileIcon />
        编辑资料
      </RouterLink>
    </li>
    <li>
      <button type="button" class="text-sm font-bold py-3 w-full text-left" @click="user.logout()">
        <UserLogoutIcon />
        退出
      </button>
    </li>
  </ul>
</div>
</template>

<style scoped>

</style>