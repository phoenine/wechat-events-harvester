import axios from 'axios'
import { getToken } from '@/utils/auth'
import { Message } from '@arco-design/web-vue'
import router from '@/router'


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
    // Message.error(errorMsg)
    return Promise.reject(errorMsg)
  }
)

export default http
