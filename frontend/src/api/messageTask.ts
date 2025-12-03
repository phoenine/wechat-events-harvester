import http from './http'
import type { MessageTask, MessageTaskUpdate } from '@/types/messageTask'

export interface ListMessageTasksParams {
  page?: number
  pageSize?: number
}

export const listMessageTasks = (params?: ListMessageTasksParams) => {
  const page = params?.page ?? 0
  const pageSize = params?.pageSize ?? 10
  const apiParams = {
    offset: page * pageSize,
    limit: pageSize,
  }
  return http.get<MessageTask>('/wx/message_tasks', { params: apiParams })
}

export const getMessageTask = (id: string) => {
  return http.get<MessageTask>(`/wx/message_tasks/${id}`)
}

export const RunMessageTask = (id: string, isTest: boolean = false) => {
  return http.get<MessageTask>(`/wx/message_tasks/${id}/run?isTest=${isTest}`)
}

export const createMessageTask = (data: MessageTaskUpdate) => {
  return http.post('/wx/message_tasks', data)
}

export const updateMessageTask = (id: string, data: MessageTaskUpdate) => {
  return http.put(`/wx/message_tasks/${id}`, data)
}

export const FreshJobApi = () => {
  return http.put(`/wx/message_tasks/job/fresh`)
}

export const FreshJobByIdApi = (id: string, data: MessageTaskUpdate) => {
  return http.put(`/wx/message_tasks/job/fresh/${id}`, data)
}

export const deleteMessageTask = (id: string) => {
  return http.delete(`/wx/message_tasks/${id}`)
}
