import http from './http'
import axios from 'axios'
import { Message } from '@arco-design/web-vue'
export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
  expires_in: number
  user: {
    id: string
    email: string
    username: string
  }
}

export const login = (data: LoginParams) => {
  const formData = new URLSearchParams()
  formData.append('username', data.username)
  formData.append('password', data.password)
  return http.post<LoginResult>('/wx/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
}

export interface VerifyResult {
  is_valid: boolean
  username: string
  expires_at?: number
}

export const verifyToken = () => {
  return http.get<VerifyResult>('/wx/auth/verify')
}
let qrCodeIntervalId: ReturnType<typeof setInterval> | null = null
let qrCodeCounter = 0

export const QRCode = () => {
  return new Promise((resolve, reject) => {
    if (qrCodeIntervalId) {
      clearInterval(qrCodeIntervalId)
      qrCodeIntervalId = null
    }
    qrCodeCounter = 0

    http
      .get('/wx/auth/qr/code')
      .then(() => {
        const maxAttempts = 120 // 约2分钟
        qrCodeIntervalId = setInterval(() => {
          qrCodeCounter++
          if (qrCodeCounter > maxAttempts) {
            if (qrCodeIntervalId) {
              clearInterval(qrCodeIntervalId)
              qrCodeIntervalId = null
            }
            reject(new Error('获取二维码超时'))
            return
          }
          http
            .get('/wx/auth/qr/url')
            .then((uRes: any) => {
              const url = uRes?.image_url || uRes?.data?.image_url
              if (url) {
                if (qrCodeIntervalId) {
                  clearInterval(qrCodeIntervalId)
                  qrCodeIntervalId = null
                }
                resolve({ code: url })
              }
            })
            .catch(() => {
              // 忽略错误，继续轮询
            })
        }, 1000)
      })
      .catch(reject)
  })
}
let interval_status_Id: ReturnType<typeof setInterval> | null = null
export const checkQRCodeStatus = () => {
  return new Promise((resolve, reject) => {
    if (interval_status_Id) {
      clearInterval(interval_status_Id)
      interval_status_Id = null
    }
    interval_status_Id = setInterval(() => {
      http
        .get('/wx/auth/qr/status')
        .then((response: any) => {
          const data = response?.data
          if (data?.login_status) {
            Message.success('授权成功')
            if (interval_status_Id) {
              clearInterval(interval_status_Id)
              interval_status_Id = null
            }
            resolve(response)
          }
        })
        .catch((err) => {
          // clearInterval(intervalId)
          // reject(err)
        })
    }, 3000)
  })
}
export const refreshToken = () => {
  console.warn('refreshToken is disabled (no refresh_token in backend).')
  return Promise.resolve(null)
}

export const logout = () => {
  return http.post('/wx/auth/logout')
}

export const getCurrentUser = () => {
  return http.get('/wx/user')
}
