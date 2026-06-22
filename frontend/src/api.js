import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export async function getDashboard() {
  return (await api.get('/dashboard')).data
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

export async function uploadFile(path, file) {
  const form = new FormData()
  form.append('file', file)
  return (await api.post(path, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 0
  })).data
}

export async function putAction(path, payload = undefined) {
  return (await api.put(path, payload)).data
}

export async function deleteAction(path) {
  return (await api.delete(path)).data
}

