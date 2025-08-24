<template>
  <ion-app>
    <ion-router-outlet />
    
    <!-- 底部导航栏 -->
    <ion-footer v-if="showTabs" class="bottom-nav">
      <div class="nav-container">
        <div class="nav-item" @click="goToHome" :class="{ active: route.path === '/home' }">
          <ion-icon name="home-outline" />
          <span>首页</span>
        </div>
        
        <div class="nav-item" @click="goToScan" :class="{ active: route.path === '/scan' }">
          <ion-icon name="scan-outline" />
          <span>扫码领奖</span>
        </div>
        
        <div class="nav-item" @click="goToMe" :class="{ active: route.path === '/me' }">
          <ion-icon name="person-outline" />
          <span>我的账户</span>
        </div>
      </div>
    </ion-footer>
  </ion-app>
</template>

<script setup lang="ts">
import { IonApp, IonRouterOutlet, IonFooter, IonIcon } from '@ionic/vue';
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUser } from './store/user';

const route = useRoute();
const router = useRouter();
const user = useUser();

// 只在登录后的页面显示底部导航栏
const showTabs = computed(() => {
  return user.user_id && route.path !== '/login' && route.path !== '/claim';
});

const goToHome = () => {
  router.push('/home');
};

const goToScan = () => {
  router.push('/scan');
};

const goToMe = () => {
  router.push('/me');
};
</script>

<style scoped>
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: #ffffff;
  border-top: 1px solid #e0e0e0;
}

.nav-container {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 8px 0;
  height: 60px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  color: #666;
}

.nav-item:hover {
  color: #3880ff;
  background: #f8f9fa;
}

.nav-item.active {
  color: #3880ff;
}

.nav-item ion-icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.nav-item span {
  font-size: 12px;
  font-weight: 500;
}
</style>
