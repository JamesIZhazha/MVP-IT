<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>ClassMint</ion-title>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <div class="home-container">
        <div class="hero-section">
          <div class="hero-icon">🎯</div>
          <h1>ClassMint 学生端</h1>
          <p>扫码领奖，轻松管理余额</p>
        </div>
        
        <div class="status-card" v-if="user.user_id">
          <ion-icon name="person-circle-outline" class="status-icon"></ion-icon>
          <div class="status-info">
            <h3>欢迎回来！</h3>
            <p>{{ user.username }}</p>
          </div>
        </div>
        
        <div class="action-section">
          <ion-button 
            expand="block" 
            @click="goToLogin" 
            color="primary"
            class="action-btn"
            v-if="!user.user_id"
          >
            <ion-icon name="log-in-outline" slot="start"></ion-icon>
            立即登录
          </ion-button>
          
          <ion-button 
            expand="block" 
            @click="goToScan" 
            color="secondary"
            class="action-btn"
            v-if="user.user_id"
          >
            <ion-icon name="scan-outline" slot="start"></ion-icon>
            开始扫码领奖
          </ion-button>
          
          <ion-button 
            expand="block" 
            @click="goToMe" 
            color="tertiary"
            class="action-btn"
            v-if="user.user_id"
          >
            <ion-icon name="wallet-outline" slot="start"></ion-icon>
            查看我的账户
          </ion-button>
          
          <ion-button 
            expand="block" 
            @click="logout" 
            color="danger"
            class="action-btn"
            v-if="user.user_id"
            fill="outline"
          >
            <ion-icon name="log-out-outline" slot="start"></ion-icon>
            退出登录
          </ion-button>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup lang="ts">
import { IonContent, IonHeader, IonPage, IonTitle, IonToolbar, IonButton, IonIcon, IonCard } from '@ionic/vue';
import { useRouter, useRoute } from 'vue-router';
import { useUser } from '../store/user';

const router = useRouter();
const route = useRoute();
const user = useUser();

const goToLogin = () => {
  router.push('/login');
};

const goToScan = () => {
  router.push('/scan');
};

const goToMe = () => {
  router.push('/me');
};

const logout = () => {
  user.set({ user_id: 0, username: '' });
  router.replace('/login');
};
</script>

<style scoped>
.home-container {
  padding: 20px;
  padding-bottom: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}

.hero-section {
  text-align: center;
  margin-bottom: 60px;
}

.hero-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.hero-section h1 {
  color: #3880ff;
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 15px 0;
}

.hero-section p {
  color: #666;
  font-size: 18px;
  margin: 0;
}

.status-card {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 16px;
  margin-bottom: 40px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  width: 100%;
  max-width: 400px;
}

.status-icon {
  font-size: 48px;
  margin-right: 20px;
  color: rgba(255, 255, 255, 0.9);
}

.status-info h3 {
  margin: 0 0 5px 0;
  font-size: 20px;
  font-weight: 600;
}

.status-info p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.action-section {
  width: 100%;
  max-width: 400px;
}

.action-btn {
  margin: 15px 0;
  --border-radius: 12px;
  --padding-top: 16px;
  --padding-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.action-btn ion-icon {
  margin-right: 8px;
}
</style>

