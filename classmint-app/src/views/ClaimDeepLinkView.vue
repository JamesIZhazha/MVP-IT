<script setup lang="ts">
import { api } from '../api/mockApi'; 
import { useUser } from '../store/user'; 
import { useRouter } from 'vue-router';
import { onMounted, ref } from 'vue'
import { 
  IonPage, 
  IonHeader, 
  IonToolbar, 
  IonTitle, 
  IonContent, 
  IonSpinner, 
  IonText,
  IonButton,
  IonIcon
} from '@ionic/vue'

const u = useUser()
const router = useRouter()
const loading = ref(true)
const message = ref('处理中...')

const goToScan = () => {
  router.push('/scan')
}

const goToMe = () => {
  router.push('/me')
}

const goHome = () => {
  router.push('/home')
}

// 新增：解析ClassMint令牌
const parseClassMintToken = (token: string) => {
  try {
    const parts = token.split('.');
    if (parts.length !== 3 || parts[0] !== 'CM1') {
      throw new Error('令牌格式错误');
    }

    const [version, payload_b64, signature] = parts;
    
    // 解码载荷数据
    const payload_bytes = atob(payload_b64 + '=='.slice((4 - payload_b64.length % 4) % 4));
    const payload = JSON.parse(payload_bytes);
    
    // 验证必要字段
    if (!payload.amount || !payload.exp || !payload.nonce) {
      throw new Error('令牌数据不完整');
    }
    
    // 检查过期时间
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp < now) {
      throw new Error('令牌已过期');
    }
    
    return payload;
  } catch (error) {
    console.error('令牌解析失败:', error);
    throw new Error('令牌格式无效');
  }
}

onMounted(async ()=>{
  const token = new URL(window.location.href).searchParams.get('token')
  if(!token) {
    message.value = '未找到令牌参数'
    setTimeout(() => router.replace('/scan'), 3000)
    return
  }
  
  try{ 
    // 解析令牌
    const tokenData = parseClassMintToken(token);
    
    // 调用API领取
    const r = await api.claim(tokenData, u.user_id)
    message.value = `领取成功！余额：${(r.balance/100).toFixed(2)} 元`
    setTimeout(() => router.replace('/me'), 3000)
  }
  catch(e:any){ 
    message.value = e.message || '领取失败'
    setTimeout(() => router.replace('/scan'), 3000)
  } finally { 
    loading.value = false 
  }
})
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>处理令牌</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content class="ion-padding">
      <div class="claim-container">
        <div class="claim-hero">
          <div class="claim-icon">🎁</div>
          <h2>令牌处理中</h2>
          <p>正在验证您的令牌...</p>
        </div>
        
        <div class="claim-status">
          <div v-if="loading" class="loading-state">
            <ion-spinner name="crescent" class="loading-spinner"></ion-spinner>
            <p>正在处理令牌...</p>
          </div>
          
          <div v-else class="result-state">
            <ion-icon 
              :name="message.includes('成功') ? 'checkmark-circle' : 'close-circle'"
              :color="message.includes('成功') ? 'success' : 'danger'"
              class="result-icon"
            ></ion-icon>
            <h3>{{ message.includes('成功') ? '处理完成' : '处理失败' }}</h3>
            <p>{{ message }}</p>
          </div>
        </div>
        
        <div class="claim-actions">
          <ion-button 
            expand="block" 
            @click="goToScan" 
            color="primary"
            class="action-btn"
            v-if="!message.includes('成功')"
          >
            <ion-icon name="scan-outline" slot="start"></ion-icon>
            重新扫码
          </ion-button>
          
          <ion-button 
            expand="block" 
            @click="goToMe" 
            color="secondary"
            class="action-btn"
            v-if="message.includes('成功')"
          >
            <ion-icon name="wallet-outline" slot="start"></ion-icon>
            查看余额
          </ion-button>
          
          <ion-button 
            expand="block" 
            @click="goHome" 
            color="medium"
            fill="outline"
            class="action-btn"
          >
            <ion-icon name="home-outline" slot="start"></ion-icon>
            返回首页
          </ion-button>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
.claim-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
  text-align: center;
}

.claim-hero {
  margin-bottom: 40px;
}

.claim-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.claim-hero h2 {
  color: #3880ff;
  font-size: 28px;
  font-weight: bold;
  margin: 0 0 15px 0;
}

.claim-hero p {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.claim-status {
  margin-bottom: 40px;
  width: 100%;
  max-width: 400px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.loading-spinner {
  width: 60px;
  height: 60px;
  --color: #3880ff;
}

.loading-state p {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.result-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.result-icon {
  font-size: 60px;
}

.result-state h3 {
  color: #333;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.result-state p {
  color: #666;
  font-size: 16px;
  margin: 0;
  line-height: 1.5;
}

.claim-actions {
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