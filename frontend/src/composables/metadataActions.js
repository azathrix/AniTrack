import { ElMessage } from 'element-plus'

export function createMetadataActions(app, deps) {
  const { postAction, apiErrorMessage } = deps

  function clearEntryEditForm() {
    Object.assign(app.entryEditForm, {
      title_cn: '',
      bangumi_id: '',
      tmdb_id: '',
      bangumi_score: 0,
      tmdb_score: 0,
      year: 0,
      month: 0,
      release_month: '',
      season_number: 1,
      episode_offset: 0,
      media_type: app.selectedEntryMediaType || app.currentMediaType || 'anime',
      region: 'jp',
      title_romaji: '',
      title_raw: '',
      poster_url: '',
      summary: '',
      tags_text: '',
      genres_text: '',
    })
    ElMessage.info('已清空编辑表单，保存后才会写入')
  }

  async function refreshEntryMetadata(item = null, domain = '', mediaType = '') {
    const entry = item || app.selectedEntry || {}
    const entryId = Number(entry.id || entry.entry_id || 0)
    if (!entryId) return
    try {
      const result = await postAction(`/entries/${entryId}/metadata/refresh`)
      ElMessage.success(result?.message || '元数据刷新任务已提交')
      await app.reload()
    } catch (error) {
      ElMessage.error(apiErrorMessage(error))
    }
  }

  return { clearEntryEditForm, refreshEntryMetadata }
}
