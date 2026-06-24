import { ElMessage } from 'element-plus'

export function createFileBrowserActions(app, deps) {
  const { getAction, postAction, apiErrorMessage } = deps

  function appendEpisodeImportFiles(items) {
    const existing = new Set((app.episodeImportLocalItems || []).map(item => item.path))
    const next = [...(app.episodeImportLocalItems || [])]
    for (const item of items) {
      if (!item?.path || item.kind !== 'video' || existing.has(item.path)) continue
      existing.add(item.path)
      next.push({
        id: `local:${Date.now()}:${next.length}:${item.path}`,
        name: item.name || item.path,
        path: item.path,
        size: item.size || 0,
      })
    }
    app.episodeImportLocalItems = next
  }

  async function browseServerFiles(path = '') {
    app.fileBrowser.loading = true
    try {
      const query = path ? `?path=${encodeURIComponent(path)}` : ''
      const result = await getAction(`/files/browse${query}`)
      app.fileBrowser.current = result.current || ''
      app.fileBrowser.parent = result.parent || ''
      app.fileBrowser.items = result.items || []
    } catch (error) {
      ElMessage.error(apiErrorMessage(error))
    } finally {
      app.fileBrowser.loading = false
    }
  }

  async function openServerFileBrowser(mode = 'video') {
    app.fileBrowser.mode = mode
    app.fileBrowser.open = true
    await browseServerFiles(app.fileBrowser.current || '')
  }

  function selectServerFile(item) {
    if (!item) return
    if (app.fileBrowser.mode === 'match') {
      if (item.kind === 'directory' && !item.selectCurrent) {
        browseServerFiles(item.path)
        return
      }
      const entryId = Number(app.selectedEntry?.id || 0)
      if (!entryId) return
      postAction(`/entries/${entryId}/match-local-files`, { path: item.path })
        .then(async result => {
          ElMessage.success(result?.message || '本地资源已匹配')
          app.fileBrowser.open = false
          await app.openEntry(entryId, app.selectedEntryDomain, app.selectedEntryMediaType)
          await app.reload()
        })
        .catch(error => ElMessage.error(apiErrorMessage(error)))
      return
    }
    if (app.fileBrowser.mode === 'episode-import-local') {
      if (item.kind === 'directory' && item.selectCurrent) {
        appendEpisodeImportFiles(app.fileBrowser.items || [])
        ElMessage.success('已加入当前目录的视频文件')
        app.fileBrowser.open = false
        return
      }
      if (item.kind === 'directory') {
        browseServerFiles(item.path)
        return
      }
      if (item.kind !== 'video') {
        ElMessage.warning('请选择视频文件')
        return
      }
      appendEpisodeImportFiles([item])
      ElMessage.success('已加入本地视频文件')
      app.fileBrowser.open = false
      return
    }
    if (item.kind === 'directory') {
      browseServerFiles(item.path)
      return
    }
    if (app.fileBrowser.mode === 'subtitle') {
      if (item.kind !== 'subtitle') {
        ElMessage.warning('请选择字幕文件')
        return
      }
      app.episodeResourceForm.subtitle_path = item.path
    } else {
      if (item.kind !== 'video') {
        ElMessage.warning('请选择视频文件')
        return
      }
      app.episodeResourceForm.local_path = item.path
    }
    app.fileBrowser.open = false
  }

  return { browseServerFiles, openServerFileBrowser, selectServerFile }
}
