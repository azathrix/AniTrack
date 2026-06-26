<script>
import { appContextComponent } from '../composables/appContext'

export default appContextComponent()
</script>

<template>
  <section v-if="view === 'dashboard'" class="mochi-dashboard-container">
    
    <!-- 1. 顶部数据胶囊 (Mochi Pro Metrics Grid - 3 Dense Columns) -->
    <div class="mochi-metrics-row">
      <div class="mochi-metric-pro-card pink">
        <div class="pro-info">
          <span class="pro-label">本周放映时长</span>
          <strong class="pro-value">14.5 <span class="pro-unit">小时</span></strong>
          <p class="pro-sub">▲ 较上周增长 12.4% 🍓</p>
        </div>
        <div class="pro-icon">⏱️</div>
      </div>

      <div class="mochi-metric-pro-card blue">
        <div class="pro-info">
          <span class="pro-label">契约同步率</span>
          <strong class="pro-value">94.2 <span class="pro-unit">%</span></strong>
          <p class="pro-sub">TMDB 数据库对接良好 🔮</p>
        </div>
        <div class="pro-icon">🔮</div>
      </div>

      <div class="mochi-metric-pro-card purple">
        <div class="pro-info">
          <span class="pro-label">本季追番全达成</span>
          <strong class="pro-value">{{ seasonalCatalogTotal }} / {{ seasonalCatalogTotal }} <span class="pro-unit">部</span></strong>
          <p class="pro-sub">零鸽番，全卡片已点亮 🏆</p>
        </div>
        <div class="pro-icon">🏆</div>
      </div>
    </div>

    <!-- 2. 中层网格 (Mochi Mid Grid: SVG Category Preference Chart + Awakening Progress Card) -->
    <div class="mochi-mid-grid">
      <!-- Donut preference chart -->
      <div class="mochi-chart-card">
        <div class="card-head-simple">
          <h4>📊 次元题材观影偏好占比</h4>
          <span class="tag-pill text-pink">2026年最新偏好</span>
        </div>
        
        <div class="donut-chart-wrapper">
          <!-- Animated SVG Donut -->
          <div class="donut-svg-box">
            <svg class="donut-svg" viewBox="0 0 36 36">
              <path class="circle-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#FFF5F6" stroke-width="3" />
              <!-- Magic/Fantasy 40% (Pink) -->
              <path class="circle-segment pink" stroke-dasharray="40, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831" fill="none" stroke="var(--ani-pink)" stroke-width="3.5" stroke-linecap="round" />
              <!-- Music/Heal 35% (Blue) -->
              <path class="circle-segment blue" stroke-dasharray="35, 100" stroke-dashoffset="-40" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831" fill="none" stroke="var(--ani-blue)" stroke-width="3.5" stroke-linecap="round" />
              <!-- Action/Shounen 25% (Purple) -->
              <path class="circle-segment purple" stroke-dasharray="25, 100" stroke-dashoffset="-75" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831" fill="none" stroke="var(--ani-purple)" stroke-width="3.5" stroke-linecap="round" />
            </svg>
            <div class="donut-center-text">
              <span class="center-label">最爱题材</span>
              <p class="center-value">魔法/奇幻</p>
            </div>
          </div>

          <!-- Legend list -->
          <div class="donut-legend">
            <div class="legend-row">
              <span class="legend-item"><span class="legend-dot pink"></span> ✨ 魔法奇幻 (40%)</span>
              <span class="legend-count">{{ Math.ceil(seasonalCatalogTotal * 0.4) }} 部</span>
            </div>
            <div class="legend-row">
              <span class="legend-item"><span class="legend-dot blue"></span> 🎵 音乐治愈 (35%)</span>
              <span class="legend-count">{{ Math.ceil(seasonalCatalogTotal * 0.35) }} 部</span>
            </div>
            <div class="legend-row">
              <span class="legend-item"><span class="legend-dot purple"></span> 🔥 热血少年 (25%)</span>
              <span class="legend-count">{{ Math.ceil(seasonalCatalogTotal * 0.25) }} 部</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Level Up Card -->
      <div class="mochi-level-card">
        <div class="card-head-simple">
          <h4>🌸 宅能量觉醒等级</h4>
          <p class="card-subtitle-small">累积追番进度和评分以充能</p>
        </div>
        
        <div class="level-showcase">
          <span class="level-emoji">🎒</span>
          <h3 class="level-title">LV.4 二次元见习神官</h3>
          <p class="level-desc">距离下一等级还需 420 经验值</p>
        </div>

        <div class="level-progress-section">
          <div class="progress-labels">
            <span>觉醒度</span>
            <span>65%</span>
          </div>
          <div class="level-progress-bar">
            <div class="progress-fill" style="width: 65%"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. 底层网格 (Mochi Bottom Grid: High-density Tasks + Radar Log Timeline) -->
    <div class="mochi-bottom-grid">
      
      <!-- 3.1 左半边：任务中心 (High-density Task Cards) -->
      <div class="mochi-tasks-panel">
        <div class="panel-header-row">
          <div class="header-titles">
            <h3>📂 异次元调度任务列表</h3>
            <p>管理自动同步、元数据抓取和缓存流水线</p>
          </div>
          <div class="header-taglines">
            <el-tag type="warning">下载中 {{ dashboard.download_overview?.active || 0 }}</el-tag>
            <el-button size="small" plain @click="openProcessorSettings">设置</el-button>
            <el-button size="small" type="primary" plain @click="clearCompletedDownloadTasks">清理已完成</el-button>
          </div>
        </div>

        <!-- Task type toggle pills -->
        <div class="task-filter-strip">
          <button :class="{ active: !selectedTaskType }" @click="selectedTaskType = ''" class="filter-pill">
            <span>全部</span>
            <span class="badge">{{ (dashboard.tasks || []).length }}</span>
          </button>
          <button
            v-for="item in taskTypeRows"
            :key="item.type"
            :class="{ active: selectedTaskType === item.type }"
            @click="selectedTaskType = item.type"
            class="filter-pill"
          >
            <span>{{ item.name }}</span>
            <span class="badge" :class="{ warning: item.running, danger: item.failed }">
              {{ item.running ? '运行' : (item.pending ? '待审' : (item.failed ? '失败' : item.total)) }}
            </span>
          </button>
        </div>

        <!-- High-density Task cards grid -->
        <div class="task-cards-list-box">
          <div v-for="row in filteredConsoleTasks" :key="row.id" class="task-card-block">
            <div class="task-block-head">
              <div class="task-block-title">
                <el-tag :type="taskTag(row.status)" size="small">{{ row.status_text || taskStatusText(row) }}</el-tag>
                <strong class="title-text">{{ row.title }}</strong>
              </div>
              <span class="type-badge">{{ row.type_name }}</span>
            </div>
            
            <div class="task-block-progress">
              <div class="progress-bar-wrapper">
                <el-progress
                  :percentage="Number(row.progress || 0)"
                  :status="row.status === 'failed' ? 'exception' : (row.status === 'completed' ? 'success' : undefined)"
                  :stroke-width="6"
                  :show-text="false"
                />
              </div>
              <span class="progress-num">{{ Number(row.progress || 0) }}%</span>
            </div>

            <div class="task-block-foot">
              <span class="foot-time">🕒 {{ row.updated_at || '-' }}</span>
              <div class="block-actions">
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
              </div>
            </div>
          </div>
          <el-empty v-if="!filteredConsoleTasks.length" description="暂无活动任务" />
        </div>
      </div>

      <!-- 3.2 右半边：扫描雷达与近期日志 (Micro Scanner & Timeline Logs) -->
      <div class="mochi-radar-logs-panel">
        
        <!-- Radar Scanning Widget -->
        <div class="mini-radar-widget">
          <div class="radar-header">
            <div class="radar-titles">
              <h4>📡 次元雷达扫描</h4>
              <span class="radar-status-dot" :class="dashboard.scanner_status?.status || 'idle'">
                <span class="pulse-ring" v-if="dashboard.scanner_status?.status === 'running'"></span>
              </span>
            </div>
            <el-button type="primary" size="small" class="radar-mini-btn" @click="runAction('/scanner/run')">
              ⚡ 立即共鸣
            </el-button>
          </div>
          <p class="radar-mini-desc">
            状态: <b class="highlight">{{ dashboard.scanner_status?.status === 'running' ? '雷达扫描中...' : '空闲待机' }}</b>
            · 时间: <span class="dim-label">{{ dashboard.scanner_status?.updated_at || '尚未扫描' }}</span>
          </p>
        </div>

        <!-- Live Log Timeline Stream (Dotted Timeline Logs) -->
        <div class="live-timeline-box">
          <div class="timeline-title-row">
            <h4>📅 次元追番实况日志</h4>
            <span class="live-badge">实时更新</span>
          </div>

          <div class="timeline-stream">
            <div class="stream-line"></div>
            
            <div class="stream-item pink">
              <span class="stream-dot"></span>
              <div class="stream-content">
                <div class="content-meta">
                  <strong>《葬送的芙莉莲》播放进度达到 21/28 话</strong>
                  <span class="time">刚刚</span>
                </div>
                <p class="comment">"完美击中泪点，芙莉莲的心路历程刻画绝了！"</p>
              </div>
            </div>

            <div class="stream-item blue">
              <span class="stream-dot"></span>
              <div class="stream-content">
                <div class="content-meta">
                  <strong>同步向导：从 Bilibili 成功导入了《我推的孩子》</strong>
                  <span class="time">1小时前</span>
                </div>
                <p class="comment">契约导入源: bilibili 个人UID [22881223]</p>
              </div>
            </div>

            <div class="stream-item purple">
              <span class="stream-dot"></span>
              <div class="stream-content">
                <div class="content-meta">
                  <strong>对神作《孤独摇滚！》留下了 ⭐⭐⭐⭐⭐ 五星好评</strong>
                  <span class="time">昨天</span>
                </div>
                <p class="comment">"Bocchi the Rock! 真正的神级社恐写照，太好笑了！"</p>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>

  </section>
</template>
