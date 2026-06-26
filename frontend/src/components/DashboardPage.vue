<script>
import { appContextComponent } from '../composables/appContext'

export default appContextComponent()
</script>

<template>
  <section v-if="view === 'dashboard'" class="content-grid">
    <!-- Row of 4 gorgeous Mochi-style Stats Cards (高颜值马卡龙卡片) -->
    <div class="metric-card">
      <div class="metric-info">
        <span class="metric-label">已收录新番契约</span>
        <strong class="metric-value">{{ seasonalCatalogTotal }} <span class="metric-unit">部</span></strong>
        <p class="metric-sub">本季度最新追看作品 🍓</p>
      </div>
      <div class="metric-icon pink">📺</div>
    </div>

    <div class="metric-card">
      <div class="metric-info">
        <span class="metric-label">就绪可观看剧集</span>
        <strong class="metric-value">{{ watchableTotal }} <span class="metric-unit">集</span></strong>
        <p class="metric-sub">随时可以开启追番派对 🍿</p>
      </div>
      <div class="metric-icon blue">🎈</div>
    </div>

    <div class="metric-card">
      <div class="metric-info">
        <span class="metric-label">本地物理契约记录</span>
        <strong class="metric-value">{{ localAssetTotal }} <span class="metric-unit">个</span></strong>
        <p class="metric-sub">次元实体数据已安全入档 💾</p>
      </div>
      <div class="metric-icon purple">🔮</div>
    </div>

    <div class="metric-card">
      <div class="metric-info">
        <span class="metric-label">高频传输通道任务</span>
        <strong class="metric-value">{{ dashboard.download_overview?.active || 0 }} <span class="metric-unit">个</span></strong>
        <p class="metric-sub">异次元资源高速下载中 📥</p>
      </div>
      <div class="metric-icon mint">🚀</div>
    </div>

    <!-- Scanner Section (重新设计的次元扫描雷达卡墙) -->
    <el-card class="span-4 console-card scanner-radar-card">
      <template #header>
        <div class="card-header-row">
          <div class="header-desc">
            <h3>📡 次元雷达扫描器</h3>
            <p>定时或手动检索订阅源，自动刮削匹配 Bangumi ID 并调度高速资源下载</p>
          </div>
          <div class="header-actions">
            <el-tag :type="dashboard.scanner_status?.status === 'failed' ? 'danger' : (dashboard.scanner_status?.status === 'running' ? 'warning' : 'success')" class="scanner-badge">
              <span class="pulse-dot" v-if="dashboard.scanner_status?.status === 'running'"></span>
              {{ scannerStatusText }}
            </el-tag>
            <el-button type="primary" class="radar-scan-btn" @click="runAction('/scanner/run')">⚡ 开启手动雷达共鸣</el-button>
          </div>
        </div>
      </template>
      <div class="scanner-status-grid">
        <div class="status-cell">
          <span class="cell-label">当前运行相位 (Status)</span>
          <strong class="cell-value status-text" :class="dashboard.scanner_status?.status || 'idle'">
            {{ dashboard.scanner_status?.status === 'running' ? '🌀 雷达极速共鸣中...' : (dashboard.scanner_status?.status === 'failed' ? '🚧 连结异常中断' : '✨ 待机中') }}
          </strong>
        </div>
        <div class="status-cell">
          <span class="cell-label">正在活动法阵 (Active Ops)</span>
          <strong class="cell-value">{{ dashboard.console_overview?.running_operation_count || 0 }} 项并行操作</strong>
        </div>
        <div class="status-cell">
          <span class="cell-label">最后连结密匙 (Last Ops ID)</span>
          <strong class="cell-value code-font">{{ dashboard.scanner_status?.operation_id || '-' }}</strong>
        </div>
        <div class="status-cell">
          <span class="cell-label">法阵复核时间 (Updated At)</span>
          <strong class="cell-value">{{ dashboard.scanner_status?.updated_at || '尚未唤醒' }}</strong>
        </div>
      </div>
    </el-card>

    <!-- Tasks section -->
    <el-card class="span-4 console-card task-console-card">
      <template #header>
        <div class="card-header-row">
          <div class="header-desc">
            <h3>📂 异次元调度任务列表</h3>
            <p>管理扫描、元数据、下载、本地状态和缓存清理的并行执行流水线</p>
          </div>
          <div class="detail-tags">
            <el-tag type="warning">下载中 {{ dashboard.download_overview?.active || 0 }}</el-tag>
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
      <div class="task-console-layout">
        <aside class="task-type-list">
          <button :class="{ active: !selectedTaskType }" @click="selectedTaskType = ''">
            <span>全部任务</span>
            <el-tag size="small">{{ (dashboard.tasks || []).length }}</el-tag>
          </button>
          <button
            v-for="item in taskTypeRows"
            :key="item.type"
            :class="{ active: selectedTaskType === item.type }"
            @click="selectedTaskType = item.type"
          >
            <span>{{ item.name }}</span>
            <el-tag size="small" :type="item.failed ? 'danger' : (item.running ? 'warning' : (item.pending ? 'info' : 'success'))">
              {{ item.running ? `${item.running} 运行` : (item.pending ? `${item.pending} 待处理` : (item.failed ? `${item.failed} 失败` : item.total)) }}
            </el-tag>
          </button>
        </aside>
        <el-table
          :data="filteredConsoleTasks"
          row-key="id"
          height="560"
          class="candidate-table task-table"
          empty-text="暂无任务"
        >
          <el-table-column label="状态" width="110">
            <template #default="{ row }"><el-tag :type="taskTag(row.status)">{{ row.status_text || taskStatusText(row) }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="type_name" label="类型" width="120" />
          <el-table-column prop="title" label="任务" min-width="220" show-overflow-tooltip />
          <el-table-column label="进度" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">
              <el-progress
                :percentage="Number(row.progress || 0)"
                :status="row.status === 'failed' ? 'exception' : (row.status === 'completed' ? 'success' : undefined)"
              />
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="190" show-overflow-tooltip>
            <template #default="{ row }">{{ row.updated_at || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.entry_id" size="small" plain @click="openQueueEntry(row)">打开</el-button>
              <el-button
                v-if="row.source === 'download' && ['pending','submitting','remote_downloading','remote_completed','local_copying','running','submitted','downloading'].includes(row.status)"
                size="small"
                type="danger"
                plain
                @click="cancelDownloadTask({ id: row.raw_id })"
              >
                取消
              </el-button>
              <el-button v-else-if="['pending','running','waiting'].includes(row.status)" size="small" type="danger" plain @click="cancelGenericTask(row)">取消</el-button>
              <el-button v-if="row.source !== 'operation' && ['pending','running','waiting'].includes(row.status)" size="small" plain @click="pauseGenericTask(row)">暂停</el-button>
              <el-button v-if="row.source !== 'operation' && row.status === 'paused'" size="small" type="primary" plain @click="resumeGenericTask(row)">继续</el-button>
              <el-button v-if="row.source === 'download' && ['failed','cancelled'].includes(row.status)" size="small" type="primary" plain @click="retryDownloadTask({ id: row.raw_id })">重试</el-button>
              <el-popconfirm v-if="['completed','failed','cancelled','skipped'].includes(row.status)" title="清理这条任务记录？" @confirm="clearGenericTask(row)">
                <template #reference>
                  <el-button size="small" plain>清理</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </section>
</template>
