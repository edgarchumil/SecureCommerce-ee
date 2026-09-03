import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api/v1',
  timeout: 10_000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

export function setAccessToken(token: string | null) {
  if (token) apiClient.defaults.headers.common.Authorization = `Bearer ${token}`
  else delete apiClient.defaults.headers.common.Authorization
}
