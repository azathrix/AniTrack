<script>
import { appContextComponent } from '../composables/appContext'

export default appContextComponent()
</script>

<template>
  <section v-if="view === 'logs'" class="logs-page">
    <div class="logs-layout-container">
      <!-- High level stats bar (横向呼吸式胶囊数据流) -->
      <div class="logs-stats-bar">
        <div class="stat-bubble error">
          <span class="emoji">❌</span>
          <div class="info">
            <span class="label">最近错误</span>
            <strong class="value">{{ logsData.console_overview?.recent_error_count || 0 }}</strong>
          </div>
        </div>
        <div class="stat-bubble warning">
          <span class="emoji">⚠️</span>
          <div class="info">
            <span class="label">最近警告</span>
            <strong class="value">{{ logsData.console_overview?.recent_warn_count || 0 }}</strong>
          </div>
        </div>
        <div class="stat-bubble info-type">
          <span class="emoji">📃</span>
          <div class="info">
            <span class="label">显示行数</span>
            <strong class="value">{{ filteredServerLogs.length || 0 }}</strong>
          </div>
        </div>
        <div class="stat-bubble filter">
          <span class="emoji">🔍</span>
          <div class="info">
            <span class="label">当前过滤</span>
            <strong class="value">{{ logKeyword || '未过滤' }}</strong>
          </div>
        </div>
      </div>

      <!-- Log Terminal Card (macOS 极光代码终端风格) -->
      <el-card class="console-card log-terminal-card">
        <template #header>
          <div class="log-toolbar">
            <div class="toolbar-title-section">
              <span class="terminal-dot red"></span>
              <span class="terminal-dot yellow"></span>
              <span class="terminal-dot green"></span>
              <span class="terminal-title">AniTrack Server Log Terminal</span>
            </div>
            <div class="toolbar-actions-section">
              <el-input v-model="logKeyword" clearable placeholder="键入关键词进行实时过滤..." class="log-search-input">
                <template #prefix>🔍</template>
              </el-input>
              <el-button type="primary" plain @click="exportLogs">📥 导出日志</el-button>
              <el-button type="danger" plain @click="runAction('/logs/clear')">🧹 清空日志</el-button>
            </div>
          </div>
        </template>
        <div class="terminal-body">
          <pre class="server-log">{{ filteredServerLogText }}</pre>
        </div>
      </el-card>
    </div>
  </section>
</template>
