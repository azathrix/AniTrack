<script>
import { appContextComponent } from '../composables/appContext'

export default appContextComponent()
</script>

<template>
  <section v-if="view === 'dashboard'" class="content-grid">
    <div class="metric-card">
      <span>新番条目</span>
      <strong>{{ dashboard.seasonal_items.length }}</strong>
    </div>
    <div class="metric-card">
      <span>可观看</span>
      <strong>{{ watchableTotal }}</strong>
    </div>
    <div class="metric-card">
      <span>本地资源</span>
      <strong>{{ localAssetTotal }}</strong>
    </div>
    <div class="metric-card">
      <span>下载任务</span>
      <strong>{{ dashboard.download_overview?.active || 0 }}</strong>
    </div>

    <el-card class="span-4 console-card scanner-card">
      <template #header>
        <div class="card-header-row">
          <div>
            <strong>扫描器</strong>
            <span>RSS 扫描、作品匹配、集数资源入库</span>
          </div>
          <div class="detail-tags">
            <el-tag :type="dashboard.scanner_status?.status === 'failed' ? 'danger' : (dashboard.scanner_status?.status === 'running' ? 'warning' : 'success')">
              {{ dashboard.scanner_status?.message || '空闲' }}
            </el-tag>
            <el-button type="primary" plain @click="runAction('/scanner/run')">扫描 RSS</el-button>
          </div>
        </div>
      </template>
      <div class="detail-summary-grid">
        <div><span>当前状态</span><strong>{{ dashboard.scanner_status?.status || 'idle' }}</strong></div>
        <div><span>最近操作</span><strong>{{ dashboard.scanner_status?.operation_id || '-' }}</strong></div>
        <div><span>更新时间</span><strong>{{ dashboard.scanner_status?.updated_at || '-' }}</strong></div>
        <div><span>运行中</span><strong>{{ dashboard.console_overview?.running_operation_count || 0 }}</strong></div>
      </div>
      <div class="scheduled-strip">
        <button
          v-for="job in dashboard.scheduled_jobs"
          :key="job.job_key"
          class="scheduled-pill"
          @click="selectedConsoleSection = `scheduler:${job.job_key}`; openScheduledSettings()"
        >
          <span>{{ job.job_key === 'rss_scan' ? 'RSS 定时扫描' : job.job_key }}</span>
          <el-tag size="small" :type="scheduledBadgeType(job.job_key)">{{ scheduledBadgeText(job.job_key) }}</el-tag>
        </button>
      </div>
    </el-card>

    <el-card class="span-4 console-card download-task-card">
      <template #header>
        <div class="card-header-row">
          <div>
            <strong>下载任务</strong>
            <span>磁力/种子提交下载器，完成后整理到本地媒体库</span>
          </div>
          <div class="detail-tags">
            <el-tag type="warning">进行中 {{ dashboard.download_overview?.active || 0 }}</el-tag>
            <el-tag v-if="dashboard.download_overview?.failed" type="danger">失败 {{ dashboard.download_overview.failed }}</el-tag>
            <el-button size="small" plain @click="openProcessorSettings">设置</el-button>
            <el-button size="small" type="primary" plain @click="clearCompletedDownloadTasks">清除已完成</el-button>
            <el-popconfirm title="取消全部下载任务？" @confirm="cancelAllDownloads">
              <template #reference>
                <el-button size="small" type="danger" plain>取消全部</el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </template>
      <el-table
        :data="dashboard.download_tasks || []"
        row-key="id"
        :expand-row-keys="expandedDownloadTaskKeys"
        height="560"
        class="candidate-table download-task-table"
        empty-text="暂无下载任务"
        @expand-change="(row, expandedRows) => { expandedDownloadTaskKeys = expandedRows.map(item => item.id) }"
      >
        <el-table-column type="expand" width="44">
          <template #default="{ row }">
            <div class="queue-task-expand">
              <section>
                <strong>资源</strong>
                <div><span>资源标题</span><code>{{ row.resource_title || '-' }}</code></div>
                <div><span>资源链接</span><code>{{ row.source_ref || row.resource_ref || '-' }}</code></div>
                <div><span>远端路径</span><code>{{ row.remote_path || '-' }}</code></div>
              </section>
              <section>
                <strong>本地整理</strong>
                <div><span>目标路径</span><code>{{ row.target_local_path || row.local_asset_path || '-' }}</code></div>
                <div><span>下载器</span><code>{{ row.provider_key || row.provider || '-' }}</code></div>
                <div><span>错误</span><code>{{ row.last_error || '-' }}</code></div>
              </section>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }"><el-tag :type="taskTag(row.status)">{{ row.status_text || taskStatusText(row) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="display_title" label="作品" min-width="220" show-overflow-tooltip />
        <el-table-column prop="episode_number" label="集" width="70" />
        <el-table-column label="阶段" width="130">
          <template #default="{ row }">{{ row.status_text || taskStatusText(row) || '-' }}</template>
        </el-table-column>
        <el-table-column label="进度" width="190">
          <template #default="{ row }">
            <el-progress
              v-if="Number(row.progress || 0) > 0"
              :percentage="Number(row.progress || 0)"
              :status="row.status === 'failed' ? 'exception' : (row.status === 'completed' ? 'success' : undefined)"
            />
            <span v-else>{{ row.progress_text || row.status_text || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="190" show-overflow-tooltip>
          <template #default="{ row }">{{ row.updated_at || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.entry_id" size="small" plain @click="openQueueEntry(row)">打开</el-button>
            <el-button v-if="row.active" size="small" type="danger" plain @click="cancelDownloadTask(row)">取消</el-button>
            <el-button v-if="row.status === 'failed' || row.status === 'cancelled'" size="small" type="primary" plain @click="retryDownloadTask(row)">重试</el-button>
            <el-popconfirm v-if="!row.active" title="删除这条下载任务记录？" @confirm="deleteDownloadTask(row)">
              <template #reference>
                <el-button size="small" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </section>
</template>
