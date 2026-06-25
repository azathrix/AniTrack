import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export async function getDashboard() {
  return (await api.get('/dashboard')).data
}

export async function getCatalog(kind, params = {}) {
  const path = kind === 'seasonal' ? '/seasonal/catalog' : `/media/${kind}/catalog`
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params || {})) {
    if (value === undefined || value === null || value === '') continue
    if (Array.isArray(value)) {
      for (const item of value) {
        if (item !== undefined && item !== null && String(item).trim() !== '') search.append(key, item)
      }
    } else {
      search.append(key, value)
    }
  }
  return (await api.get(path, { params: search })).data
}

export async function getCalendar(params = {}) {
  return (await api.get('/calendar', { params })).data
}

export async function getLogs() {
  return (await api.get('/logs')).data
}

export async function getAction(path) {
  return (await api.get(path)).data
}

export async function getSettings() {
  return (await api.get('/settings')).data
}

export async function getDiagnostics() {
  return (await api.get('/system/diagnostics')).data
}

export async function saveSettings(payload) {
  return (await api.put('/settings', payload)).data
}

export async function getMediaItem(type, id) {
  return (await api.get(`/media/${type}/${id}`)).data
}

export async function saveMediaItem(type, id, payload) {
  return (await api.put(`/media/${type}/${id}`, payload)).data
}

export async function postAction(path, payload = undefined) {
  return (await api.post(path, payload)).data
}

export async function uploadFile(path, file, fields = {}, onProgress = null) {
  const form = new FormData()
  form.append('file', file)
  for (const [key, value] of Object.entries(fields || {})) {
    if (value !== undefined && value !== null) form.append(key, value)
  }
  return (await api.post(path, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 0,
    onUploadProgress: onProgress || undefined,
  })).data
}

export async function putAction(path, payload = undefined) {
  return (await api.put(path, payload)).data
}

export async function deleteAction(path) {
  return (await api.delete(path)).data
}

