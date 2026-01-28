import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user.js'
import HomepageIndex from "@/views/homepage/HomepageIndex.vue"
import FriendIndex from "@/views/friend/FriendIndex.vue"
import CreateIndex from "@/views/create/CreateIndex.vue"
import LoginIndex from "@/views/user/account/LoginIndex.vue"
import RegisterIndex from "@/views/user/account/RegisterIndex.vue"
import SpaceIndex from "@/views/user/space/SpaceIndex.vue"
import ProfileIndex from "@/views/profile/ProfileIndex.vue"
import NotFoundIndex from "@/views/error/NotFoundIndex.vue"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', component: HomepageIndex, name: 'homepage-index', meta: { needLogin: false } },
    { path: '/friend', component: FriendIndex, name: 'friend-index', meta: { needLogin: true } },
    { path: '/create', component: CreateIndex, name: 'create-index', meta: { needLogin: true } },
    { path: '/login', component: LoginIndex, name: 'login-index', meta: { needLogin: false } },
    { path: '/register', component: RegisterIndex, name: 'register-index', meta: { needLogin: false } },
    { path: '/user/space', component: SpaceIndex, name: 'space-index', meta: { needLogin: true } },
    { path: '/profile', component: ProfileIndex, name: 'profile-index', meta: { needLogin: true } },
    { path: '/:pathMatch(.*)*', component: NotFoundIndex, name: 'not-found' },
  ],
})

router.beforeEach((to, from, next) => {
  const user = useUserStore()

  const needLogin = to.meta.needLogin

  // 需要登录的页面且当前未登录，跳转到登录页，并记录原目标地址
  if (needLogin && !user.isLogin()) {
    return next({
      name: 'login-index',
      query: { redirect: to.fullPath },
    })
  }

  // 已登录用户访问登录/注册页面时，直接跳到首页
  if (user.isLogin() && (to.name === 'login-index' || to.name === 'register-index')) {
    return next({ name: 'homepage-index' })
  }

  return next()
})

export default router
