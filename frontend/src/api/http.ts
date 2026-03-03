import axios from 'axios'
import { getToken } from '@/utils/auth'
import { Message } from '@arco-design/web-vue'
import router from '@/router'

const WX_AUTH_HINT_EVENT = 'wx-auth-required'

const extractErrorText = (payload: any): string => {
  if (!payload) return ''
  if (typeof payload === 'string') return payload
  if (typeof payload?.message === 'string') return payload.message
  if (typeof payload?.detail === 'string') return payload.detail
  if (typeof payload?.detail?.message === 'string') return payload.detail.message
  return ''
}

const isWxAuthRelatedError = (text: string): boolean => {
  const msg = String(text || '')
  if (!msg) return false
  return (
    msg.includes('当前环境异常') ||
    msg.includes('完成验证后即可继续访问') ||
    msg.includes('登录态异常') ||
    msg.includes('请先扫码登录公众号平台') ||
    msg.includes('Invalid Session')
  )
}

const notifyWxAuthRequired = (reason: string) => {
  window.dispatchEvent(
    new CustomEvent(WX_AUTH_HINT_EVENT, {
      detail: { reason },
    })
  )
}

// 创建axios实例
const http = axios.create({
  baseURL: '/api/v1/',
  timeout: 100000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// 请求拦截器
http.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers = config.headers || {}
      ;(config.headers as any)['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response) => {
    // 兼容非统一响应结构：如登录接口直接返回 token 对象
    if (response.status >= 200 && response.status < 300 && response.data?.code === undefined) {
      return response.data
    }
    // 处理标准响应格式
    if (response.data?.code === 0) {
      return response.data?.data || response.data?.detail || response.data || response
    }
    if (response.data?.code == 401) {
      router.push('/login')
      return Promise.reject('未登录或登录已过期，请重新登录。')
    }
    const data = response.data?.detail || response.data
    const errorMsg = data?.message || '请求失败'
    if (isWxAuthRelatedError(extractErrorText(data))) {
      notifyWxAuthRequired(extractErrorText(data))
      return Promise.reject(data)
    }
    const contentType = response.headers['content-type'] || response.headers['Content-Type']
    const isJson = typeof contentType === 'string' && contentType.includes('application/json')
    if (isJson) {
      Message.error(errorMsg)
      return Promise.reject(data)
    } else {
      // 非 JSON 响应（如文件流等），直接返回原始数据
      return response.data
    }
  },
  (error) => {
    const status = error?.response?.status
    if (status === 401) {
      router.push('/login')
    }
    // 统一错误处理
    const errorMsg =
      error?.response?.data?.message ||
      error?.response?.data?.detail?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      '请求错误'
    if (isWxAuthRelatedError(String(errorMsg))) {
      notifyWxAuthRequired(String(errorMsg))
    }
    // Message.error(errorMsg)
    return Promise.reject(errorMsg)
  }
)

export default http
