<script>
import { appContextComponent } from '../composables/appContext'

export default appContextComponent()
</script>

<template>
      <section v-if="view === 'calendar'" class="calendar-page">
        <div class="toolbar calendar-toolbar">
          <el-date-picker
            v-model="calendarWeek"
            type="week"
            format="[第] ww [周] YYYY"
            value-format="YYYY-MM-DD"
            placeholder="选择周"
          />
          <el-button-group>
            <el-button @click="shiftCalendarWeek(-1)">上一周</el-button>
            <el-button @click="setCalendarThisWeek">本周</el-button>
            <el-button @click="shiftCalendarWeek(1)">下一周</el-button>
          </el-button-group>
        </div>
        <div class="calendar-day-tabs">
          <button
            v-for="day in weekDays"
            :key="day.key"
            :class="{ active: selectedCalendarDay === day.key, today: day.isToday }"
            @click="selectedCalendarDay = day.key"
          >
            <strong>{{ day.label }}</strong>
            <span>{{ day.dateLabel }}</span>
            <em v-if="day.isToday">今天</em>
            <b v-if="day.items.length">{{ day.items.length }}</b>
          </button>
        </div>
        <div class="calendar-selected-panel">
          <div v-if="selectedCalendarItems.length" class="calendar-update-grid">
            <article
              v-for="item in selectedCalendarItems"
              :key="`${selectedCalendarDayData.key}-${item.entry_id}-${item.episode_number}-${item.updated_at}`"
              class="calendar-update-card"
              @click="openEntry(item.entry_id, 'seasonal', 'anime')"
            >
              <div class="calendar-update-cover">
                <img v-if="item.poster_url" :src="item.poster_url" />
                <span v-else>{{ (item.work_display_title || item.entry_display_title || item.display_title || 'AN').slice(0, 2) }}</span>
              </div>
              <div class="calendar-update-meta">
                <strong>{{ item.work_display_title || item.entry_display_title || item.display_title }}</strong>
                <span>{{ item.entry_scope_label || item.entry_secondary_title || '-' }}</span>
                <div>
                  <el-tag size="small" type="primary">第 {{ item.episode_number || '?' }} 集</el-tag>
                  <el-tag size="small" type="warning">已更新</el-tag>
                  <el-tag v-if="item.synced" size="small" type="success">可观看</el-tag>
                </div>
              </div>
            </article>
          </div>
          <el-empty v-else description="这一天没有更新" />
        </div>
      </section>

</template>

