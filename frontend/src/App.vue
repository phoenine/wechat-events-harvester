<template>
  <a-layout class="app-container">
    <!-- 头部 -->
    <a-layout-header class="app-header" v-if="route.path !== '/login'">
      <div class="header-left">
        <div class="logo">
          <img :src="logo" alt="avatar" :width="40" style="margin-right:1rem;">
          <router-link to="/">{{ appTitle }}</router-link>
          <a-tooltip
            v-if="hasLogined"
            :content="haswxLogined ? '已授权' : '未授权，请扫码登录'"
            position="bottom"
          >
            <span style="display: inline-flex; align-items: center; margin-left: 10px;">
              <icon-scan
                v-if="!haswxLogined"
                @click="showAuthQrcode()"
                :style="{ cursor: 'pointer', color: '#F53F3F' }"
              />
              <span v-else style="display: inline-flex; align-items: center;">
                <icon-check-circle :style="{ color: '#00B42A' }" />
                <span style="margin-right: 4px; color: #00B42A; font-size: 13px;">
                  已授权
                </span>
              </span>
            </span>
          </a-tooltip>
        </div>
      </div>
      <div class="header-right" v-if="hasLogined">
        <a-select
          :defaultValue="currentLanguage"
          v-model:value="currentLanguage"
          @change="handleLanguageChange"
          style="width: 150px; margin-right: 20px;"
        >
          <a-option value="chinese_simplified">简体中文</a-option>
          <a-option value="chinese_traditional">繁體中文</a-option>
          <a-option value="english" selected="selected">English</a-option>
        </a-select>
        <a-link href="/api/docs" target="_blank" style="margin-right: 20px;">Docs</a-link>
        <a-tooltip content="您的支持是作者的最大动力，来一杯咖啡吧" position="bottom">
          <a-link @click="showSponsorModal" style="margin-right: 20px; cursor: pointer;" type="text">支持</a-link>
        </a-tooltip>
        <a-link href="https://www.paypal.com/ncp/payment/PUA72WYLAV5KW" target="_blank"
          style="margin-right: 20px;">赞助</a-link>



        <a-dropdown position="br" trigger="click">
          <div class="user-info">
            <a-avatar :size="36">
              <img :src="avatarSrc" alt="avatar" @error="handleAvatarError">
            </a-avatar>
            <span class="username">{{ displayName }}</span>
          </div>
          <template #content>
            <a-doption @click="goToEditUser">
              <template #icon><icon-user /></template>
              个人中心
            </a-doption>
            <a-doption @click="goToChangePassword">
              <template #icon><icon-lock /></template>
              修改密码
            </a-doption>
            <a-doption @click="showAuthQrcode">
              <template #icon><icon-scan /></template>
              刷新授权
            </a-doption>
            <a-doption @click="handleLogout">
              <template #icon><icon-user /></template>
              退出登录
            </a-doption>
          </template>
        </a-dropdown>
        <WechatAuthQrcode ref="qrcodeRef" @success="handleWxAuthSuccess" />
        <a-modal v-model:visible="sponsorVisible" title="感谢支持" :footer="false" :style="{ zIndex: 1000 }" unmount-on-close>
          <div style="text-align: center;">
            <p>如果您觉得这个项目对您有帮助,请给Rachel来一杯Coffee吧~ </p>
            <img src="@/assets/images/sponsor.jpg" alt="赞赏码" style="max-width: 300px; margin-top: 20px;">
          </div>
        </a-modal>
      </div>
    </a-layout-header>

    <a-layout>

      <!-- 主内容区 -->
      <a-layout>
        <a-layout-content class="app-content">
          <router-view />
        </a-layout-content>
      </a-layout>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import translate from 'i18n-jsautotranslate'
import { ref,watchEffect, computed, onMounted, onBeforeUnmount, watch, provide } from 'vue'
import { Modal } from '@arco-design/web-vue/es/modal'
import {getSysInfo} from '@/api/sysInfo'
const currentLanguage = ref(localStorage.getItem('language') || 'chinese_simplified');


const handleLanguageChange = (language: string) => {
  setCurrentLanguage(language);
  currentLanguage.value = language;
};

const sponsorVisible = ref(false)
const showSponsorModal = (e: Event) => {
  e.preventDefault()
  sponsorVisible.value = true
  console.log('Sponsor modal triggered') // 添加调试日志
}
import { useRouter, useRoute } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getCurrentUser } from '@/api/auth'
import { logout } from '@/api/auth'
import WechatAuthQrcode from '@/components/WechatAuthQrcode.vue'

const qrcodeRef = ref()
const showAuthQrcode = () => {
  qrcodeRef.value?.startAuth()
}
provide('showAuthQrcode', showAuthQrcode)
const onWxAuthRequired = () => {
  Message.warning('检测到授权异常，请重新扫码授权')
  showAuthQrcode()
}
const appTitle = computed(() => import.meta.env.VITE_APP_TITLE || '微信活动订阅助手')
const logo = ref("/logo.svg")
const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const userInfo = ref({
  username: '',
  nickname: '',
  avatar: ''
})
const DEFAULT_AVATAR = '/default-avatar.png'
const avatarSrc = ref(DEFAULT_AVATAR)
const displayName = computed(() => userInfo.value.nickname || userInfo.value.username || '')
const haswxLogined = ref(false)
const hasLogined = ref(false)
const isAuthenticated = computed(() => {
  hasLogined.value = !!localStorage.getItem('token')
  return hasLogined.value
})

const fetchUserInfo = async () => {
  try {
    const res = await getCurrentUser()
    userInfo.value = {
      username: res?.username || '',
      nickname: res?.nickname || '',
      avatar: res?.avatar || ''
    }
    avatarSrc.value = userInfo.value.avatar || DEFAULT_AVATAR
  } catch (error) {
    console.error('获取用户信息失败', error)
    avatarSrc.value = DEFAULT_AVATAR
  }
}

const handleAvatarError = () => {
  avatarSrc.value = DEFAULT_AVATAR
}

const fetchSysInfo = async () => {
  try {
    const res = await getSysInfo()
    haswxLogined.value = res?.wx?.login||false
  } catch (error) {
    console.error('获取系统信息失败', error)
  }
}

const handleWxAuthSuccess = async () => {
  // 先立即更新 UI，再向后端确认最终状态
  haswxLogined.value = true
  await fetchSysInfo()
}

const handleCollapse = (val: boolean) => {
  collapsed.value = val
}

const handleMenuClick = (key: string) => {
  router.push({ name: key })
}

const goToEditUser = () => {
  router.push({ name: 'EditUser' })
}

const goToChangePassword = () => {
  router.push({ name: 'ChangePassword' })
}

const handleLogout = async () => {
  try {
    await logout()
    localStorage.removeItem('token')
    router.push('/login')
  } catch (error) {
    Message.error('退出登录失败')
  }
}

onMounted(() => {
  window.addEventListener('wx-auth-required', onWxAuthRequired as EventListener)
  if (isAuthenticated.value) {
    fetchUserInfo()
    fetchSysInfo()
  }
  translatePage();
})

onBeforeUnmount(() => {
  window.removeEventListener('wx-auth-required', onWxAuthRequired as EventListener)
})
import { translatePage, setCurrentLanguage } from '@/utils/translate';

watch(
  () => route.path,
  () => {
    hasLogined.value = !!localStorage.getItem('token')
    if (hasLogined.value) {
      fetchUserInfo()
      fetchSysInfo()
    }
  }
)
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}


.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 64px;
  background: var(--color-bg-2);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 500;
}

.logo svg {
  margin-right: 10px;
  font-size: 24px;
  color: var(--primary-color);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 10px;
}

.app-content {
  /* padding: 20px; */
  background: var(--color-bg-1);
  min-height: calc(100vh - 64px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 720px) {
  .app-header .header-right {
    display: none !important;
  }
}
</style>
