<script setup lang="ts">
import { api } from '../api/mockApi'
import { useUser } from '../store/user'
import { useRouter } from 'vue-router'
import { ref, onMounted, onActivated, computed } from 'vue'
import { 
  IonPage, 
  IonHeader, 
  IonToolbar, 
  IonTitle, 
  IonContent, 
  IonCard, 
  IonCardHeader, 
  IonCardContent, 
  IonList, 
  IonItem, 
  IonLabel, 
  IonBadge,
  IonButton,
  IonIcon,
  IonNote,
  IonSpinner
} from '@ionic/vue'

const u = useUser()
const router = useRouter()
const refreshing = ref(false)

// 使用计算属性从全局状态获取数据
const balance = computed(() => u.balance)
const recent = computed(() => u.recent)

const load = async () => { 
  try {
    const r = await api.balance(u.user_id)
    u.updateBalance(r.balance, r.recent)
  } catch (error) {
    console.error('Failed to load balance:', error)
  }
}

const refreshBalance = async () => {
  refreshing.value = true
  await load()
  refreshing.value = false
}

const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 2592000000) return `${Math.floor(diff / 86400000)}天前`
  
  return date.toLocaleDateString()
}

const goToScan = () => {
  router.push('/scan')
}

const logout = () => {
  u.clear()
  router.replace('/login')
}

onMounted(load)
onActivated(load)
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>我的账户</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content class="ion-padding">
      <div class="me-container">
        <!-- 用户信息卡片 -->
        <div class="user-card">
          <div class="user-avatar">
            <ion-icon name="person-circle-outline"></ion-icon>
          </div>
          <div class="user-info">
            <h3>{{ u.username }}</h3>
            <p>学生用户</p>
          </div>
        </div>
        
        <!-- 余额卡片 -->
        <div class="balance-card">
          <div class="balance-header">
            <h3>当前余额</h3>
            <ion-icon name="wallet-outline" class="balance-icon"></ion-icon>
          </div>
          <div class="balance-amount">
            <span class="currency">¥</span>
            <span class="amount">{{ (balance/100).toFixed(2) }}</span>
          </div>
          <div class="balance-footer">
            <ion-button 
              fill="clear" 
              size="small" 
              @click="refreshBalance"
              :disabled="refreshing"
            >
              <ion-icon name="refresh-outline" slot="start"></ion-icon>
              {{ refreshing ? '刷新中...' : '刷新' }}
            </ion-button>
          </div>
        </div>
        
        <!-- 交易记录 -->
        <div class="transactions-section">
          <div class="section-header">
            <h3>最近交易</h3>
            <ion-badge color="primary">{{ recent.length }}</ion-badge>
          </div>
          
          <div v-if="recent.length === 0" class="empty-state">
            <ion-icon name="receipt-outline" class="empty-icon"></ion-icon>
            <p>暂无交易记录</p>
            <ion-note>扫码领奖后，交易记录将显示在这里</ion-note>
          </div>
          
          <div v-else class="transaction-list">
            <div 
              v-for="(tx, i) in recent" 
              :key="i" 
              class="transaction-item"
              :class="{ 'earn': tx.type === 'earn', 'redeem': tx.type === 'redeem' }"
            >
              <div class="transaction-icon">
                <ion-icon 
                  :name="tx.type === 'earn' ? 'add-circle' : 'remove-circle'"
                  :color="tx.type === 'earn' ? 'success' : 'danger'"
                ></ion-icon>
              </div>
              
              <div class="transaction-details">
                <h4>{{ tx.type === 'earn' ? '领取奖励' : '扣减' }}</h4>
                <p class="transaction-time">{{ formatTime(tx.created_at) }}</p>
                <p v-if="tx.token" class="transaction-token">令牌: {{ tx.token }}</p>
              </div>
              
              <div class="transaction-amount">
                <span 
                  class="amount"
                  :class="{ 'positive': tx.type === 'earn', 'negative': tx.type === 'redeem' }"
                >
                  {{ tx.type === 'earn' ? '+' : '-' }}¥{{ (tx.amount/100).toFixed(2) }}
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 快速操作 -->
        <div class="quick-actions">
          <ion-button 
            expand="block" 
            @click="goToScan" 
            color="primary"
            class="action-btn"
          >
            <ion-icon name="scan-outline" slot="start"></ion-icon>
            继续扫码领奖
          </ion-button>
          
          <ion-button 
            expand="block" 
            @click="logout" 
            color="danger"
            fill="outline"
            class="action-btn"
          >
            <ion-icon name="log-out-outline" slot="start"></ion-icon>
            退出登录
          </ion-button>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
.me-container {
  padding: 20px;
  padding-bottom: 100px;
}

.user-card {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px;
  border-radius: 20px;
  margin-bottom: 25px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.user-avatar ion-icon {
  font-size: 60px;
  margin-right: 20px;
  color: rgba(255, 255, 255, 0.9);
}

.user-info h3 {
  margin: 0 0 5px 0;
  font-size: 24px;
  font-weight: 600;
}

.user-info p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.balance-card {
  background: white;
  border-radius: 20px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
}

.balance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.balance-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.balance-icon {
  font-size: 24px;
  color: #3880ff;
}

.balance-amount {
  text-align: center;
  margin-bottom: 20px;
}

.currency {
  font-size: 24px;
  color: #666;
  margin-right: 5px;
}

.amount {
  font-size: 48px;
  font-weight: bold;
  color: #3880ff;
}

.balance-footer {
  text-align: center;
}

.transactions-section {
  background: white;
  border-radius: 20px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  border: 1px solid #f0f0f0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 60px;
  color: #ccc;
  margin-bottom: 20px;
}

.empty-state p {
  color: #666;
  font-size: 16px;
  margin: 0 0 10px 0;
}

.empty-state ion-note {
  font-size: 14px;
  color: #999;
}

.transaction-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.transaction-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 12px;
  border-left: 4px solid transparent;
}

.transaction-item.earn {
  border-left-color: #2dd36f;
  background: #f0fff4;
}

.transaction-item.redeem {
  border-left-color: #eb445a;
  background: #fff5f5;
}

.transaction-icon {
  margin-right: 15px;
}

.transaction-icon ion-icon {
  font-size: 24px;
}

.transaction-details {
  flex: 1;
}

.transaction-details h4 {
  margin: 0 0 5px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.transaction-time {
  margin: 0 0 3px 0;
  font-size: 14px;
  color: #666;
}

.transaction-token {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.transaction-amount {
  text-align: right;
}

.transaction-amount .amount {
  font-size: 18px;
  font-weight: 600;
}

.transaction-amount .positive {
  color: #2dd36f;
}

.transaction-amount .negative {
  color: #eb445a;
}

.quick-actions {
  margin-top: 30px;
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