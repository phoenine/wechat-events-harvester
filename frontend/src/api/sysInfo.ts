import http from './http'

export const getSysInfo = () => http.get('/wx/sys/info')

export const getSysResources = () => http.get('/wx/sys/resources')
