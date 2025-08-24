import { createRouter, createWebHistory } from '@ionic/vue-router';
import type { RouteRecordRaw } from 'vue-router';

// ✅ 懒加载视图（按需）：保持你原来 HomePage 也可继续存在
const HomePage    = () => import('../views/HomePage.vue');          // 你已有
const LoginView   = () => import('../views/LoginView.vue');         // 新增
const ScanView    = () => import('../views/ScanView.vue');          // 新增
const MeView      = () => import('../views/MeView.vue');            // 新增
const ClaimDeepLinkView = () => import('../views/ClaimDeepLinkView.vue'); // 可选

const routes: Array<RouteRecordRaw> = [
  { path: '/', redirect: '/home' },              // 默认进首页
  { path: '/home', name: 'Home', component: HomePage },

  // 新增的三个核心页面
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/scan',  name: 'Scan',  component: ScanView },
  { path: '/me',    name: 'Me',    component: MeView },

  // 可选：用于 aukash:// 或 https://.../claim?token=... 深链直达领取
  { path: '/claim', name: 'ClaimDeepLink', component: ClaimDeepLinkView },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// ✅ 登录拦截：未登录只能访问 /login
import { useUser } from '../store/user';

router.beforeEach((to) => {
  // 确保 store 已经初始化
  try {
    const u = useUser();
    if (!u.user_id && to.path !== '/login') {
      return '/login';
    }
  } catch (error) {
    // 如果 store 还没初始化，允许访问登录页
    if (to.path !== '/login') {
      return '/login';
    }
  }
  return true;
});

export default router;