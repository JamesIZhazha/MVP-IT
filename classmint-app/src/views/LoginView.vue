<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../api/mockApi'
import { useRouter } from 'vue-router'
import { useUser } from '../store/user'
import { 
  IonPage, 
  IonHeader, 
  IonToolbar, 
  IonTitle, 
  IonContent, 
  IonItem, 
  IonInput, 
  IonButton, 
  IonText, 
  IonNote,
  IonSpinner,
  IonIcon,
  IonLabel
} from '@ionic/vue'

const router = useRouter()
const user = useUser()
const username = ref('student')
const password = ref('123456')
const msg = ref('')
const isLoading = ref(false)

async function doLogin() {
  if (isLoading.value) return
  
  try {
    isLoading.value = true
    msg.value = ''
    
    console.log('开始登录，用户名:', username.value, '密码:', password.value)
    const result = await api.login(username.value, password.value)
    console.log('登录API返回结果:', result)
    
    if (result.ok) {
      console.log('登录成功，用户ID:', result.user_id)
      user.set({ user_id: result.user_id, username: username.value })
      
      // 登录成功后初始化余额和交易记录
      try {
        console.log('开始获取余额，用户ID:', result.user_id)
        const balanceResult = await api.balance(result.user_id)
        console.log('余额API返回结果:', balanceResult)
        user.updateBalance(balanceResult.balance, balanceResult.recent)
        console.log('余额更新成功')
      } catch (error) {
        console.error('初始化余额失败:', error)
      }
      
      msg.value = '登录成功！'
      
      setTimeout(() => {
        router.replace('/scan')
      }, 1000)
    } else {
      console.log('登录失败，结果:', result)
      msg.value = '账号或密码错误'
    }
  } catch (error: any) {
    console.error('登录过程中发生错误:', error)
    msg.value = error.message || '登录失败'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>登录</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content class="ion-padding">
      <div class="login-container">
        <div class="logo-section">
          <div class="logo">🎯</div>
          <h1>ClassMint</h1>
          <p>扫码领奖系统</p>
        </div>
        
        <div class="form-section">
          <ion-item class="form-item">
            <ion-label position="stacked">账号</ion-label>
            <ion-input 
              v-model="username" 
              placeholder="请输入账号" 
              class="custom-input"
            />
          </ion-item>
          
          <ion-item class="form-item">
            <ion-label position="stacked">密码</ion-label>
            <ion-input 
              v-model="password" 
              type="password" 
              placeholder="请输入密码" 
              class="custom-input"
            />
          </ion-item>
          
          <ion-button 
            expand="block" 
            @click="doLogin" 
            color="primary"
            class="login-btn"
            :disabled="isLoading"
          >
            <ion-spinner v-if="isLoading" name="crescent"></ion-spinner>
            {{ isLoading ? '登录中...' : '登录' }}
          </ion-button>
          
          <ion-text color="danger" v-if="msg" class="error-msg">
            {{ msg }}
          </ion-text>
          
          <div class="demo-info">
            <ion-note>
              <ion-icon name="information-circle-outline"></ion-icon>
              测试账号：student / 123456
            </ion-note>
          </div>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
.login-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
}

.logo-section {
  text-align: center;
  margin: 40px 0 60px 0;
}

.logo {
  font-size: 80px;
  margin-bottom: 20px;
}

.logo-section h1 {
  color: #3880ff;
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 10px 0;
}

.logo-section p {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.form-section {
  flex: 1;
}

.form-item {
  margin-bottom: 20px;
  --border-radius: 12px;
  --background: #f8f9fa;
  --border-color: transparent;
}

.form-item:focus-within {
  --background: #ffffff;
  --border-color: #3880ff;
  --border-width: 2px;
}

.custom-input {
  --padding-start: 16px;
  --padding-end: 16px;
  --padding-top: 12px;
  --padding-bottom: 12px;
  font-size: 16px;
}

.login-btn {
  margin: 30px 0 20px 0;
  --border-radius: 12px;
  --padding-top: 16px;
  --padding-bottom: 16px;
  font-size: 18px;
  font-weight: 600;
}

.error-msg {
  display: block;
  text-align: center;
  margin: 20px 0;
  font-size: 14px;
}

.demo-info {
  text-align: center;
  margin-top: 30px;
}

.demo-info ion-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.demo-info ion-icon {
  font-size: 16px;
  color: #3880ff;
}
</style>