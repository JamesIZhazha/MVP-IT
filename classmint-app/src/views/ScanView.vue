<script setup lang="ts">
import { api } from '../api/mockApi'
import { useUser } from '../store/user'
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  IonPage, 
  IonHeader, 
  IonToolbar, 
  IonTitle, 
  IonContent, 
  IonButton, 
  IonText, 
  IonNote,
  IonIcon,
  IonModal,
  IonSegment,
  IonSegmentButton,
  IonLabel,
  IonCard,
  IonCardHeader,
  IonCardTitle,
  IonCardContent,
  IonList,
  IonItem,
  IonLabel as IonItemLabel,
  IonBadge,
  IonAlert,
  IonToast
} from '@ionic/vue'

let jsQR: any = null

const user = useUser(); 
const router = useRouter();
const msg = ref(''); 
const scanning = ref(false)
const showCameraModal = ref(false)
const cameraStream = ref<MediaStream | null>(null)
const videoElement = ref<HTMLVideoElement | null>(null)
const canvasElement = ref<HTMLCanvasElement | null>(null)
const isCameraActive = ref(false)
const isProcessing = ref(false)
const currentBalance = ref(0)

// 新增：令牌解析相关
const showTokenModal = ref(false)
const parsedToken = ref<any>(null)
const tokenError = ref('')

const toast = (t:string) => { 
  msg.value = t; 
  setTimeout(() => msg.value = '', 3000) 
}

// 修改：支持新的二维码格式解析
const extract = (s:string) => { 
  // 支持两种格式：
  // 1. 完整URL: https://classmint.local/claim?token=CM1.xxx.xxx
  // 2. 纯令牌: CM1.xxx.xxx
  
  if (s.startsWith('https://classmint.local/claim?token=')) {
    // 从URL中提取令牌
    const m = s.match(/[?&]token=([^&]+)/); 
    return m ? decodeURIComponent(m[1]) : null;
  } else if (s.startsWith('CM1.')) {
    // 直接是令牌格式
    return s;
  } else if (s && s.length > 3) {
    // 兼容旧格式
    return s;
  }
  return null;
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
    
    return {
      version,
      payload,
      signature,
      amount_yuan: payload.amount / 100,
      expires_at: new Date(payload.exp * 1000).toLocaleString('zh-CN'),
      is_expired: payload.exp < now,
      description: payload.desc || '无说明'
    };
  } catch (error) {
    console.error('令牌解析失败:', error);
    throw new Error('令牌格式无效');
  }
}

// 新增：处理扫描到的二维码
const handleScannedQR = async (qrData: string) => {
  try {
    isProcessing.value = true;
    
    // 提取令牌
    const token = extract(qrData);
    if (!token) {
      throw new Error('无法识别的二维码格式');
    }
    
    // 解析令牌
    const parsed = parseClassMintToken(token);
    parsedToken.value = parsed;
    
    // 清除之前的错误信息
    tokenError.value = '';
    
    // 显示令牌信息（不自动领取）
    showTokenModal.value = true;
    
  } catch (error: any) {
    // 只有在真正出错时才设置错误信息
    tokenError.value = error.message || '二维码解析失败';
    showTokenModal.value = true;
  } finally {
    isProcessing.value = false;
  }
}

// 新增：确认领取令牌
const confirmClaim = async () => {
  try {
    if (!parsedToken.value) {
      throw new Error('无效的令牌数据');
    }
    
    // 调用本地API领取
    const result = await api.claim(parsedToken.value.payload, user.user_id);
    
    // 更新余额
    await getCurrentBalance();
    
    // 显示成功消息
    toast(`领取成功！获得 ¥${parsedToken.value.amount_yuan.toFixed(2)}`);
    
    // 关闭令牌信息模态框
    showTokenModal.value = false;
    
    // 关闭摄像头（如果还在扫描）
    if (showCameraModal.value) {
      closeCameraModal();
    }
    
    // 跳转到我的页面
    setTimeout(() => {
      router.push('/me');
    }, 1500);
    
  } catch (error: any) {
    // 显示错误信息
    if (error.message.includes('已使用')) {
      toast('该令牌已被使用，无法重复领取');
    } else if (error.message.includes('已过期')) {
      toast('该令牌已过期，无法领取');
    } else {
      toast(error.message || '领取失败');
    }
    
    // 关闭令牌信息模态框
    showTokenModal.value = false;
    
    // 关闭摄像头（如果还在扫描）
    if (showCameraModal.value) {
      closeCameraModal();
    }
  }
}

const getCurrentBalance = async () => {
  try {
    const result = await api.balance(user.user_id)
    currentBalance.value = result.balance
    // 同时更新全局状态
    user.updateBalance(result.balance, result.recent)
    return result.balance
  } catch (error) {
    console.error('获取余额失败:', error)
    return 0
  }
}

const initBalance = async () => {
  await getCurrentBalance()
}

// 使用计算属性从全局状态获取余额
const displayBalance = computed(() => user.balance || currentBalance.value)

const loadJsQR = async () => {
  if (jsQR) return jsQR
  
  try {
    if (typeof window !== 'undefined' && !(window as any).jsQR) {
      const script = document.createElement('script')
      script.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js'
      script.onload = () => {
        jsQR = (window as any).jsQR
        console.log('jsQR库加载成功')
      }
      script.onerror = () => {
        console.error('jsQR库加载失败')
        toast('二维码识别库加载失败')
      }
      document.head.appendChild(script)
      
      return new Promise((resolve) => {
        script.onload = () => {
          jsQR = (window as any).jsQR
          console.log('jsQR库加载成功')
          resolve(jsQR)
        }
      })
    } else if ((window as any).jsQR) {
      jsQR = (window as any).jsQR
      return jsQR
    }
    
    return jsQR
  } catch (error) {
    console.error('加载jsQR库失败:', error)
    toast('二维码识别库加载失败')
    return null
  }
}

const startCameraScan = async () => {
  try {
    msg.value = '正在启动摄像头...'
    
    const qrLibrary = await loadJsQR()
    if (!qrLibrary) {
      toast('无法加载二维码识别库')
      return
    }
    
    const stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        facingMode: 'environment',
        width: { ideal: 1280 },
        height: { ideal: 720 }
      } 
    })
    
    cameraStream.value = stream
    showCameraModal.value = true
    
    setTimeout(() => {
      if (videoElement.value) {
        videoElement.value.srcObject = stream
        videoElement.value.play()
        isCameraActive.value = true
        msg.value = '摄像头已启动，请将二维码对准屏幕'
        
        startScanningLoop()
      }
    }, 100)
    
  } catch (error: any) {
    console.error('启动摄像头失败:', error)
    if (error.name === 'NotAllowedError') {
      toast('需要摄像头权限')
      msg.value = '需要摄像头权限，请在设置中允许应用使用摄像头'
    } else if (error.name === 'NotFoundError') {
      toast('未找到摄像头设备')
      msg.value = '未找到摄像头设备，请检查设备摄像头是否正常'
    } else {
      toast('启动摄像头失败')
      msg.value = `启动摄像头失败: ${error.message}`
    }
  }
}

const startScanningLoop = () => {
  if (!isCameraActive.value || !videoElement.value || !canvasElement.value) return
  
  console.log('开始扫描循环')
  
  const scanFrame = () => {
    if (!isCameraActive.value || isProcessing.value) {
      if (isCameraActive.value && !isProcessing.value) {
        setTimeout(() => {
          startScanningLoop()
        }, 100)
      }
      return
    }
    
    try {
      const video = videoElement.value!
      const canvas = canvasElement.value!
      const ctx = canvas.getContext('2d')!
      
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      
      if (jsQR) {
        let code = null
        
        code = jsQR(imageData.data, imageData.width, imageData.height, {
          inversionAttempts: "attemptBoth",
          maxAttempts: 3,
        })
        
        if (!code) {
          const centerX = Math.floor(imageData.width / 2)
          const centerY = Math.floor(imageData.height / 2)
          const scanSize = Math.min(imageData.width, imageData.height) * 0.6
          
          const startX = Math.max(0, centerX - scanSize / 2)
          const startY = Math.max(0, centerY - scanSize / 2)
          const endX = Math.min(imageData.width, startX + scanSize)
          const endY = Math.min(imageData.height, startY + scanSize)
          
          const centerImageData = ctx.getImageData(startX, startY, endX - startX, endY - startY)
          
          code = jsQR(centerImageData.data, centerImageData.width, centerImageData.height, {
            inversionAttempts: "attemptBoth",
            maxAttempts: 2,
          })
        }
        
        if (!code) {
          const enhancedData = new Uint8ClampedArray(imageData.data)
          for (let i = 0; i < enhancedData.length; i += 4) {
            const gray = (enhancedData[i] + enhancedData[i + 1] + enhancedData[i + 2]) / 3
            const enhanced = Math.min(255, gray * 1.2)
            enhancedData[i] = enhancedData[i + 1] = enhancedData[i + 2] = enhanced
          }
          
          code = jsQR(enhancedData, imageData.width, imageData.height, {
            inversionAttempts: "attemptBoth",
            maxAttempts: 2,
          })
        }
        
        if (code) {
          console.log('识别到二维码:', code.data)
          handleScannedQR(code.data)
          return
        }
      }
      
      setTimeout(() => {
        if (isCameraActive.value && !isProcessing.value) {
          requestAnimationFrame(scanFrame)
        }
      }, 20)
      
    } catch (error) {
      console.error('扫描帧处理失败:', error)
      setTimeout(() => {
        if (isCameraActive.value && !isProcessing.value) {
          requestAnimationFrame(scanFrame)
        }
      }, 100)
    }
  }
  
  scanFrame()
}

const stopCamera = () => {
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(track => track.stop())
    cameraStream.value = null
  }
  isCameraActive.value = false
  showCameraModal.value = false
  isProcessing.value = false
}

const closeCameraModal = () => {
  stopCamera()
}

onMounted(() => {
  initBalance()
})
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>扫码领奖</ion-title>
      </ion-toolbar>
    </ion-header>
    
    <ion-content class="ion-padding">
      <div class="scan-container">
        <div class="scan-hero">
          <div class="scan-icon">📱</div>
          <h2>扫码领奖</h2>
          <p>扫描二维码，快速领取奖励</p>
          <div class="balance-display">
            <ion-icon name="wallet-outline"></ion-icon>
            <span class="balance-text">当前余额：{{ (displayBalance/100).toFixed(2) }} 元</span>
          </div>
        </div>
        
        <div class="scan-section">
          <ion-button 
            expand="block" 
            @click="startCameraScan()" 
            color="primary"
            class="scan-btn"
            size="large"
          >
            <ion-icon name="scan-outline" slot="start"></ion-icon>
            开始实时扫描
          </ion-button>
          
          <div class="scan-status" v-if="msg">
            <ion-icon 
              :name="msg.includes('成功') ? 'checkmark-circle' : 
                     msg.includes('失败') ? 'close-circle' : 'information-circle'" 
              :color="msg.includes('成功') ? 'success' : 
                      msg.includes('失败') ? 'danger' : 'medium'"
            ></ion-icon>
            <span>{{ msg }}</span>
          </div>
        </div>
      </div>
    </ion-content>
    
    <ion-modal :is-open="showCameraModal" @did-dismiss="closeCameraModal">
      <ion-header>
        <ion-toolbar>
          <ion-title>扫码领奖</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeCameraModal">
              <ion-icon name="close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      
      <ion-content class="ion-padding">
        <div class="camera-container">
          <div class="camera-preview">
            <video 
              ref="videoElement"
              class="camera-video"
              autoplay
              playsinline
              muted
            ></video>
            
            <div class="scan-frame">
              <div class="scan-corner top-left"></div>
              <div class="scan-corner top-right"></div>
              <div class="scan-corner bottom-left"></div>
              <div class="scan-corner bottom-right"></div>
            </div>
            
            <div class="scan-hint">
              <ion-icon name="scan-outline"></ion-icon>
              <p>将二维码对准扫描框</p>
              <div class="scan-indicator" v-if="isCameraActive && !isProcessing">
                <div class="scan-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
                <p class="scan-text">正在扫描中...</p>
              </div>
            </div>
          </div>
          
          <canvas 
            ref="canvasElement" 
            style="display: none;"
            width="1280"
            height="720"
          ></canvas>
          
          <div class="camera-controls">
            <ion-button 
              expand="block" 
              @click="closeCameraModal" 
              color="danger"
              fill="outline"
              class="control-btn"
            >
              <ion-icon name="close-outline" slot="start"></ion-icon>
              关闭摄像头
            </ion-button>
          </div>
          
          <div class="camera-status" v-if="msg">
            <ion-icon 
              :name="msg.includes('成功') ? 'checkmark-circle' : 'information-circle'" 
              :color="msg.includes('成功') ? 'success' : 'medium'"
            ></ion-icon>
            <span>{{ msg }}</span>
          </div>
        </div>
      </ion-content>
    </ion-modal>

    <!-- 令牌信息模态框 -->
    <ion-modal :is-open="showTokenModal" @did-dismiss="showTokenModal = false">
      <ion-header>
        <ion-toolbar>
          <ion-title>领取奖励</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="showTokenModal = false">
              <ion-icon name="close"></ion-icon>
            </ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content class="ion-padding">
        <ion-card v-if="parsedToken">
          <ion-card-header>
            <ion-card-title>奖励详情</ion-card-title>
          </ion-card-header>
          <ion-card-content>
            <ion-list>
              <ion-item>
                <ion-item-label>奖励金额</ion-item-label>
                <ion-badge color="success">{{ parsedToken.amount_yuan }} 元</ion-badge>
              </ion-item>
              <ion-item>
                <ion-item-label>过期时间</ion-item-label>
                <ion-badge color="danger">{{ parsedToken.expires_at }}</ion-badge>
              </ion-item>
              <ion-item>
                <ion-item-label>描述</ion-item-label>
                <ion-badge color="info">{{ parsedToken.description }}</ion-badge>
              </ion-item>
            </ion-list>
            <ion-button expand="block" color="primary" @click="confirmClaim">
              确认领取
            </ion-button>
          </ion-card-content>
        </ion-card>
        <!-- 只在有错误时才显示错误提示 -->
        <ion-alert
          v-if="tokenError"
          :is-open="showTokenModal && tokenError"
          header="领取失败"
          :message="tokenError"
          buttons="Dismiss"
          @did-dismiss="tokenError = ''"
        ></ion-alert>
      </ion-content>
    </ion-modal>
  </ion-page>
</template>

<style scoped>
.scan-container {
  padding: 20px;
  padding-bottom: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}

.scan-hero {
  text-align: center;
  margin-bottom: 60px;
}

.scan-icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.scan-hero h2 {
  color: #3880ff;
  font-size: 28px;
  font-weight: bold;
  margin: 0 0 15px 0;
}

.scan-hero p {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.balance-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
  color: #666;
  font-size: 14px;
}

.balance-display ion-icon {
  font-size: 20px;
}

.balance-text {
  font-weight: 500;
}

.scan-section {
  width: 100%;
  max-width: 400px;
}

.scan-btn {
  --border-radius: 16px;
  --padding-top: 20px;
  --padding-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.scan-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 12px;
  margin-top: 20px;
}

.scan-status ion-icon {
  font-size: 20px;
}

.scan-status span {
  color: #666;
  font-size: 14px;
}

.camera-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.camera-preview {
  position: relative;
  flex: 1;
  background: #000;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 20px;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scan-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 250px;
  height: 250px;
  border: 2px solid rgba(255, 255, 255, 0.8);
  border-radius: 16px;
}

.scan-corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 3px solid #3880ff;
}

.scan-corner.top-left {
  top: -3px;
  left: -3px;
  border-right: none;
  border-bottom: none;
  border-top-left-radius: 8px;
}

.scan-corner.top-right {
  top: -3px;
  right: -3px;
  border-left: none;
  border-bottom: none;
  border-top-right-radius: 8px;
}

.scan-corner.bottom-left {
  bottom: -3px;
  left: -3px;
  border-right: none;
  border-top: none;
  border-bottom-left-radius: 8px;
}

.scan-corner.bottom-right {
  bottom: -3px;
  right: -3px;
  border-left: none;
  border-top: none;
  border-bottom-right-radius: 8px;
}

.scan-hint {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  color: white;
  background: rgba(0, 0, 0, 0.7);
  padding: 10px 20px;
  border-radius: 20px;
}

.scan-hint ion-icon {
  font-size: 24px;
  margin-bottom: 5px;
  display: block;
}

.scan-hint p {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.scan-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.scan-dots {
  display: flex;
  gap: 5px;
}

.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  background-color: #3880ff;
  border-radius: 50%;
  animation: pulse 1.5s infinite ease-in-out;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
.dot:nth-child(3) { animation-delay: 0s; }

@keyframes pulse {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.7; }
  40% { transform: translateY(-10px); opacity: 1; }
}

.scan-text {
  margin: 0;
  font-size: 14px;
  color: white;
  font-weight: 500;
}

.camera-controls {
  margin-bottom: 20px;
}

.control-btn {
  --border-radius: 12px;
  --padding-top: 16px;
  --padding-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.camera-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 12px;
  margin-top: 20px;
}

.camera-status ion-icon {
  font-size: 20px;
}

.camera-status span {
  color: #666;
  font-size: 14px;
}
</style>