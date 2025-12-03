import http from './http'

export interface UploadFileResult {
  code: number
  url: string
}

export const uploadFile = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<UploadFileResult>('/wx/user/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
