import { AxiosRequestConfig } from 'axios'
import { request } from './request'

/**
 * Creative Agent - 创意生成 API
 */
export function creativeGenerate(
  params: {
    query: string
    session_id?: string
  },
  options?: AxiosRequestConfig,
) {
  return request.post<ReadableStream>('/creative/generate', params, {
    headers: {
      Accept: 'text/event-stream',
    },
    responseType: 'stream',
    adapter: 'fetch',
    loading: false,
    ...options,
  })
}
