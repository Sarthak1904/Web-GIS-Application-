import { api, apiFormData } from './client'

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface Dataset {
  id: number
  name: string
  slug: string
  description: string | null
  created_at: string
}

export interface DatasetVersion {
  id: number
  dataset_id: number
  version: number
  status: string
  crs: string
  created_at: string
}

export interface GeoFeature {
  type: 'Feature'
  id?: number
  geometry: GeoJSON.Geometry
  properties: Record<string, unknown>
}

export interface FeatureCollection {
  type: 'FeatureCollection'
  features: GeoFeature[]
  total: number
}

export const authApi = {
  login: (username: string, password: string) =>
    api<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => api<{ id: number; username: string; email: string }>('/auth/me'),
}

export const datasetsApi = {
  list: (includeDeleted = false) =>
    api<Dataset[]>(`/datasets${includeDeleted ? '?include_deleted=true' : ''}`),
  get: (id: number) => api<Dataset>(`/datasets/${id}`),
  versions: (id: number) => api<DatasetVersion[]>(`/datasets/${id}/versions`),
  create: (data: { name: string; slug: string; description?: string }) =>
    api<Dataset>('/datasets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  delete: (id: number, permanent = false) =>
    api<{ message: string }>(`/datasets/${id}/delete${permanent ? '?permanent=true' : ''}`, {
      method: 'POST',
    }),
}

export const featuresApi = {
  query: (params: {
    dataset_version_id: number
    bbox?: string
    limit?: number
    offset?: number
  }) => {
    const search = new URLSearchParams()
    search.set('dataset_version_id', String(params.dataset_version_id))
    if (params.bbox) search.set('bbox', params.bbox)
    if (params.limit) search.set('limit', String(params.limit))
    if (params.offset) search.set('offset', String(params.offset))
    return api<FeatureCollection>(`/features?${search}`)
  },
}

export const uploadApi = {
  shapefile: (datasetId: number, file: File) => {
    const form = new FormData()
    form.append('dataset_id', String(datasetId))
    form.append('file', file)
    return apiFormData<{ job_id: number; task_id: string; dataset_version_id: number; status: string }>(
      '/upload/shapefile',
      form
    )
  },
}
