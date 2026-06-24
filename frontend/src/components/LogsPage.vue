<script>
import { appContextComponent } from '../composables/appContext'

export default appContextComponent()
</script>

<template>
      <section v-if="view === 'logs'" class="logs-page">
        <div class="logs-layout">
          <el-card class="console-card log-page-card">
            <template #header>
              <div class="card-header-row">
                <div>
                  <strong>服务日志</strong>
                  <span>查看、搜索和导出运行日志</span>
                </div>
                <el-tag :type="logsBadgeType">{{ logsBadgeText }}</el-tag>
              </div>
            </template>
            <div class="detail-summary-grid">
              <div><span>最近错误</span><strong>{{ dashboard.console_overview?.recent_error_count || 0 }}</strong></div>
              <div><span>最近警告</span><strong>{{ dashboard.console_overview?.recent_warn_count || 0 }}</strong></div>
              <div><span>显示行数</span><strong>{{ filteredServerLogs.length || 0 }}</strong></div>
              <div><span>筛选</span><strong>{{ logKeyword || '全部' }}</strong></div>
            </div>
            <div class="log-console">
              <div class="log-toolbar">
                <el-input v-model="logKeyword" clearable placeholder="搜索日志" />
                <el-button plain @click="exportLogs">导出日志</el-button>
                <el-button plain @click="runAction('/logs/clear')">清空日志</el-button>
              </div>
              <pre class="server-log">{{ filteredServerLogText }}</pre>
            </div>
          </el-card>
        </div>
      </section>

</template>

