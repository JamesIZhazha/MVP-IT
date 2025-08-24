# 🎯 ClassMint 学生端 APP

一个基于 Ionic + Vue 3 + Capacitor 的移动端应用，实现"扫码领奖 + 余额显示 + 账号密码登录"的闭环演示。

## ✨ 功能特性

- 🔐 **账号密码登录**：本地校验（student/123456）
- 📱 **扫码领奖**：支持 DEMO-100 / DEMO-500 令牌
- 💰 **余额管理**：实时余额显示和最近 10 笔流水
- 🔗 **深度链接**：支持 `/claim?token=...` 直接领取
- 📱 **响应式设计**：完美适配移动端和桌面端
- 💾 **本地存储**：使用 localStorage 模拟数据库

## 🚀 快速开始

### 环境要求

- Node.js 16+
- npm 或 yarn
- Android Studio（用于 Android 构建）

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

### 构建 Android 应用

```bash
npm run build
npx cap sync android
npx cap open android
```

## 📱 页面导航

| 路径 | 页面 | 功能 |
|------|------|------|
| `/` | 首页 | 欢迎页面，显示当前状态 |
| `/login` | 登录页 | 账号密码登录 |
| `/scan` | 扫码页 | 扫码领奖功能 |
| `/me` | 账户页 | 余额和交易记录 |
| `/claim` | 深度链接页 | 处理 claim?token=... |

## 🧪 演示流程

1. **登录**：访问 `/login`，使用 `student/123456` 登录
2. **扫码**：登录成功后跳转到 `/scan`，点击"开始扫码"
3. **领奖**：扫描包含令牌的二维码
4. **查看余额**：访问 `/me` 查看余额增加和交易记录

## 🏗️ 项目结构

```
src/
├── views/                 # 页面组件
│   ├── HomePage.vue      # 首页
│   ├── LoginView.vue     # 登录页
│   ├── ScanView.vue      # 扫码页
│   ├── MeView.vue        # 账户页
│   └── ClaimDeepLinkView.vue # 深度链接页
├── store/                # 状态管理
│   └── user.ts          # 用户状态
├── api/                  # API 接口
│   └── mockApi.ts       # 模拟 API
├── mock/                 # 模拟数据
│   └── db.ts            # 本地数据库
└── router/               # 路由配置
    └── index.ts         # 路由定义
```

## 🔧 技术栈

- **前端框架**：Vue 3 + Composition API
- **UI 组件库**：Ionic Vue 8
- **状态管理**：Pinia
- **路由**：Vue Router 4
- **构建工具**：Vite
- **移动端**：Capacitor 7
- **扫码功能**：@capacitor-mlkit/barcode-scanning

## 📋 验收标准

- ✅ 登录成功进入扫码页
- ✅ 扫码 DEMO-500 后余额 +5.00 元
- ✅ 再扫提示"令牌已使用"
- ✅ "我的账户"可见最近流水，时间正确
- ✅ 页面无空白，主要流程无报错

## 🐛 常见问题

### PowerShell 执行策略限制

如果遇到 `npm run dev` 执行失败，请：

```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy RemoteSigned

# 或者临时绕过
Set-ExecutionPolicy Bypass -Scope Process
```

### 扫码权限问题

首次使用扫码功能需要授予相机权限，请确保：

1. 在浏览器中允许相机权限
2. 在移动设备上授予应用相机权限

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
