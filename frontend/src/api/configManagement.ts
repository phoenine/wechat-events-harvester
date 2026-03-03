import http from './http'
import type { ConfigManagement, ConfigManagementUpdate } from '@/types/configManagement'

export interface ListConfigsParams {
  page?: number
  pageSize?: number
}

export const listConfigs = (params?: ListConfigsParams) => {
  const page = params?.page ?? 1
  const pageSize = params?.pageSize ?? 10
  const apiParams = {
    offset: Math.max(0, page - 1) * pageSize,
    limit: pageSize,
  }
  return http.get<ConfigManagement>('/wx/configs', { params: apiParams })
}
export const getConfig = (key: string) => {
  return http.get<ConfigManagement>(`/wx/configs/${key}`)
}

export const createConfig = (data: ConfigManagementUpdate) => {
  return http.post('/wx/configs', data)
}

export const updateConfig = (key: string, data: ConfigManagementUpdate) => {
  return http.put(`/wx/configs/${key}`, data)
}

export const deleteConfig = (key: string) => {
  return http.delete(`/wx/configs/${key}`)
}
