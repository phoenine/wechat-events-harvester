import http from './http'

export interface ExportArticlesParams {
  mp_id: string
  scope?: 'selected' | 'all'
  ids?: string[]
  limit?: number
  page_count?: number
  add_title?: boolean
  remove_images?: boolean
  remove_links?: boolean
  format: string[]
  zip_filename?: string
}

export interface ExportRecordsParams {
  mp_id: string
}

export interface DeleteExportRecordsParams {
  mp_id?: string
  filename: string
}

export const exportArticles = (params: ExportArticlesParams) => {
  const requestData = {
    mp_id: params.mp_id,
    doc_id: params.scope === 'selected' ? params.ids ?? [] : [],
    page_size: params.limit ?? 10,
    page_count: params.page_count ?? 1,
    // 默认为添加标题；显式传 false 时要保留 false
    add_title: params.add_title ?? true,
    remove_images: params.remove_images ?? false,
    remove_links: params.remove_links ?? false,
    export_md: params.format?.includes('md') ?? false,
    export_docx: params.format?.includes('docx') ?? false,
    export_json: params.format?.includes('json') ?? false,
    export_csv: params.format?.includes('csv') ?? false,
    export_pdf: params.format?.includes('pdf') ?? false,
    zip_filename: params.zip_filename ?? '',
  }
  return http.post<{ code: number; data: string }>('/wx/tools/export/articles', requestData, {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
    },
  })
}

export const getExportRecords = (params: ExportRecordsParams) => {
  const requestData = {
    mp_id: params.mp_id,
  }
  return http.get<{ code: number; data: string }>('/wx/tools/export/list', {
    params: requestData,
  })
}

export const DeleteExportRecords = (params: DeleteExportRecordsParams) => {
  const requestData = {
    mp_id: params.mp_id ?? '',
    filename: params.filename,
  }
  return http.delete<{ code: number; data: string }>('/wx/tools/export/delete', {
    data: requestData,
  })
}
