<script>
import draggable from 'vuedraggable'
import { appContextComponent } from '../composables/appContext'
import PriorityList from './PriorityList.vue'

export default appContextComponent({ draggable, PriorityList })
</script>

<template>
      <section v-if="view === 'settings'">
        <el-card>
          <template #header>全局设置</template>
          <el-form :model="settings" label-position="top" class="settings-form">
            <el-tabs>
              <el-tab-pane label="基础">
                <el-alert
                  type="info"
                  show-icon
                  :closable="false"
                  title="RSS 订阅入口在新番页；这里保留代理、补全和命名规则等全局行为。"
                  class="settings-alert"
                />
                <div class="settings-card-container">
                  <div class="settings-card-item">
                    <div class="card-item-header">
                      <h3>🌐 RSS 网络传送代理</h3>
                      <p>为雷达扫描与订阅推送定制网络代理主机，高效穿透异次元阻碍</p>
                    </div>
                    <el-form-item label="RSS 代理主机配置">
                      <el-input v-model="settings.rss_proxy" placeholder="例: http://NAS_IP:20171 (留空则直连)" class="custom-rounded-input" />
                    </el-form-item>
                  </div>

                  <div class="settings-card-item">
                    <div class="card-item-header">
                      <h3>🔑 TMDB 异次元密匙 (Token)</h3>
                      <p>连结影视巨量网络数据库，用于番剧、电影及电视剧的名称智能刮削与高清封面同步</p>
                    </div>
                    <el-form-item label="TMDB 开放平台安全 Token">
                      <el-input v-model="settings.tmdb_token" placeholder="请输入您的 TMDB 访问令牌 (API Read Access Token)..." show-password class="custom-rounded-input" />
                    </el-form-item>
                  </div>

                  <div class="settings-card-item">
                    <div class="card-item-header">
                      <h3>🍓 新季番剧自动化补全</h3>
                      <p>当雷达侦测到有新发布时，智能往回追溯扫描，补全当前季度由于网络、发布延迟缺失的集数</p>
                    </div>
                    <div class="switch-row-item">
                      <span class="switch-desc-label">自动激活并补全本季缺失剧集</span>
                      <el-switch v-model="settings.backfill_current_season" />
                    </div>
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="自动选择">
                <el-tabs tab-position="left" class="nested-settings-tabs">
                  <el-tab-pane label="动画">
                    <div class="settings-section-toolbar">
                      <div>
                        <strong>动画自动选集</strong>
                        <span>用于新番和番剧的资源优先级</span>
                      </div>
                      <el-button plain @click="resetSelectionRules('anime')">重置动画规则</el-button>
                    </div>
                    <div class="priority-layout">
                      <PriorityList title="字幕组优先级" v-model="settings.subtitle_priority" placeholder="添加字幕组" />
                      <PriorityList title="分辨率优先级" v-model="settings.resolution_priority" placeholder="添加分辨率" />
                      <PriorityList title="主字幕语言优先级" v-model="settings.language_priority" placeholder="添加主字幕语言" />
                      <PriorityList title="副字幕语言优先级" v-model="settings.secondary_language_priority" placeholder="添加副字幕语言" />
                    </div>
                  </el-tab-pane>
                  <el-tab-pane label="电影">
                    <div class="settings-section-toolbar">
                      <div>
                        <strong>电影自动选集</strong>
                        <span>只影响电影页面 and 电影导入资源</span>
                      </div>
                      <el-button plain @click="resetSelectionRules('movie')">重置电影规则</el-button>
                    </div>
                    <div class="priority-layout">
                      <PriorityList title="画质优先级" v-model="settings.movie_quality_priority" placeholder="添加画质，如 2160p" />
                      <PriorityList title="来源优先级" v-model="settings.movie_source_priority" placeholder="添加来源，如 BluRay" />
                      <PriorityList title="字幕优先级" v-model="settings.movie_subtitle_priority" placeholder="添加字幕，如 简体" />
                    </div>
                  </el-tab-pane>
                  <el-tab-pane label="电视剧">
                    <div class="settings-section-toolbar">
                      <div>
                        <strong>电视剧自动选集</strong>
                        <span>只影响电视剧页面 and 电视剧导入资源</span>
                      </div>
                      <el-button plain @click="resetSelectionRules('tv')">重置电视剧规则</el-button>
                    </div>
                    <div class="priority-layout">
                      <PriorityList title="画质优先级" v-model="settings.tv_quality_priority" placeholder="添加画质，如 1080p" />
                      <PriorityList title="来源优先级" v-model="settings.tv_source_priority" placeholder="添加来源，如 WEB-DL" />
                      <PriorityList title="字幕优先级" v-model="settings.tv_subtitle_priority" placeholder="添加字幕，如 双语" />
                    </div>
                  </-priority-layout>
                  </el-tab-pane>
                </el-tabs>
              </el-tab-pane>
              <el-tab-pane label="下载器">
                <div class="downloader-settings">
                  <draggable v-model="settings.downloaders" item-key="id" handle=".drag-handle" class="downloader-list">
                    <template #item="{ element, index }">
                      <div class="downloader-row">
                        <span class="drag-handle">⋮⋮</span>
                        <span class="rank">{{ index + 1 }}</span>
                        <div class="downloader-fields">
                          <el-select v-model="element.type" class="downloader-type">
                            <el-option label="PikPak rclone" value="pikpak_rclone" />
                            <el-option label="PikPak API" value="pikpak_api" />
                            <el-option label="aria2" value="aria2" />
                            <el-option label="qBittorrent" value="qb" />
                          </el-select>
                          <el-input v-model="element.name" placeholder="名称" />
                          <el-input v-model="element.remote_dir" placeholder="远端目录 / 临时目录" />
                          <template v-if="element.type === 'pikpak_rclone'">
                            <el-input v-model="element.rclone_remote" placeholder="rclone remote，例如 pikpak" />
                            <el-input v-model="element.rclone_config_path" placeholder="rclone.conf 路径" />
                            <el-input v-model="element.rclone_command" placeholder="rclone 命令" />
                            <el-input v-model="element.username" placeholder="PikPak 用户名，可用于初始化 rclone" />
                            <el-input v-model="element.password" placeholder="PikPak 密码" show-password />
                          </template>
                          <template v-if="element.type === 'pikpak_api'">
                            <el-select v-model="element.auth_mode" placeholder="认证方式">
                              <el-option label="Token" value="token" />
                              <el-option label="账号密码" value="password" />
                            </el-select>
                            <template v-if="element.auth_mode === 'password'">
                              <el-input v-model="element.username" placeholder="PikPak 用户名" />
                              <el-input v-model="element.password" placeholder="PikPak 密码" show-password />
                            </template>
                            <template v-else>
                              <el-input v-model="element.access_token" placeholder="access token" show-password />
                              <el-input v-model="element.refresh_token" placeholder="refresh token" show-password />
                            </template>
                            <el-input v-model="element.proxy" placeholder="代理，可选" />
                          </template>
                          <template v-if="['aria2', 'qb'].includes(element.type)">
                            <el-input v-model="element.rpc_url" placeholder="RPC / Web UI 地址" />
                          </template>
                          <el-input
                            v-if="element.type === 'aria2'"
                            v-model="element.token"
                            placeholder="aria2 token"
                            show-password
                          />
                          <template v-if="element.type === 'qb'">
                            <el-input v-model="element.username" placeholder="qB 用户名" />
                            <el-input v-model="element.password" placeholder="qB 密码" show-password />
                          </template>
                        </div>
                        <el-switch v-model="element.enabled" />
                        <el-button type="danger" link @click="removeDownloader(index)">删除</el-button>
                      </div>
                    </template>
                  </draggable>
                  <el-button plain @click="addDownloader">添加下载器</el-button>
                </div>
              </el-tab-pane>
              <el-tab-pane label="搜索源">
                <el-alert
                  type="info"
                  show-icon
                  :closable="false"
                  title="发现页和本季补全会按优先级使用启用的搜索源。第一版优先支持 Mikan/RSS 和 Torznab/Prowlarr/Jackett。"
                  class="settings-alert"
                />
                <div class="search-source-layout">
                  <div class="search-source-list" v-loading="searchSourcesLoading">
                    <div v-for="item in searchSources" :key="item.id" class="search-source-row" :class="{ disabled: !Number(item.enabled || 0) }">
                      <div>
                        <strong>{{ item.name }}</strong>
                        <span>{{ item.kind }} · 优先级 {{ item.priority || 0 }}</span>
                        <small v-if="item.last_error">{{ item.last_error }}</small>
                      </div>
                      <div class="rss-row-actions">
                        <el-switch :model-value="Number(item.enabled || 0)" :active-value="1" :inactive-value="0" @change="toggleSearchSource(item)" />
                        <el-button type="primary" link @click="openSearchSourceDialog(item.id)">编辑</el-button>
                        <el-popconfirm title="确定删除该搜索源？" @confirm="deleteSearchSource(item.id)">
                          <template #reference><el-button type="danger" link>删除</el-button></template>
                        </el-popconfirm>
                      </div>
                    </div>
                    <el-empty v-if="!searchSources.length" description="暂无搜索源" />
                  </div>
                  <div class="search-source-form">
                    <el-button type="primary" @click="openSearchSourceDialog(null)">添加 Mikan RSS 搜索源</el-button>
                    <el-button type="primary" @click="openTorznabDialog">添加 Torznab/Prowlarr 搜索源</el-button>
                  </div>
                </div>
              </el-tab-pane>
              <el-tab-pane label="定时任务">
                <el-alert
                  type="info"
                  show-icon
                  :closable="false"
                  title="定时器控制系统自动同步、补全和下载等后台行为间隔。"
                  class="settings-alert"
                />
                <div class="schedule-settings-list">
                  <div v-for="item in dashboard.schedules || []" :key="item.id" class="schedule-settings-row">
                    <div>
                      <strong>{{ item.name || item.action_name || item.action }}</strong>
                      <span>{{ item.action_name || item.action }} · {{ Number(item.interval_minutes || 0) }} 分钟</span>
                    </div>
                    <el-tag :type="Number(item.enabled || 0) ? 'success' : 'info'">{{ Number(item.enabled || 0) ? '启用' : '关闭' }}</el-tag>
                    <el-tag v-if="item.last_status" :type="item.last_status === 'failed' ? 'danger' : 'info'">{{ item.last_status }}</el-tag>
                    <span class="schedule-run-at">{{ item.last_run_at || '未执行' }}</span>
                    <el-button plain @click="triggerSchedule(item)">立即执行</el-button>
                    <el-button type="primary" plain @click="openScheduledSettings(item)">设置</el-button>
                  </div>
                  <el-empty v-if="!(dashboard.schedules || []).length" description="暂无定时器" />
                </div>
              </el-tab-pane>
              <el-tab-pane label="维护">
                <!-- Status dashboard row (高颜值横向状态块) -->
                <div class="maintenance-stats-bar">
                  <div class="m-stat-box pink">
                    <span class="m-label">⏳ 待处理任务</span>
                    <strong class="m-value">{{ dashboard.console_overview?.pending_task_count || 0 }}</strong>
                  </div>
                  <div class="m-stat-box red">
                    <span class="m-label">⚠️ 失败任务</span>
                    <strong class="m-value">{{ dashboard.console_overview?.failed_task_count || 0 }}</strong>
                  </div>
                  <div class="m-stat-box purple">
                    <span class="m-label">🔄 等待重试</span>
                    <strong class="m-value">{{ dashboard.console_overview?.waiting_retry_count || 0 }}</strong>
                  </div>
                  <div class="m-stat-box blue">
                    <span class="m-label">⚡ 运行中队列</span>
                    <strong class="m-value">{{ dashboard.console_overview?.running_queue_count || 0 }}</strong>
                  </div>
                </div>

                <!-- Structured Action Groups (三大功能维护净化舱) -->
                <div class="maintenance-grid-layout">
                  <!-- Group 1: Cache Control -->
                  <div class="maintenance-group-card">
                    <div class="group-header">
                      <h3>🧹 缓存净化舱</h3>
                      <p>管理系统临时索引、元数据与静态网页缓存</p>
                    </div>
                    <div class="group-body">
                      <div class="action-item-row">
                        <div class="action-desc">
                          <strong>清除 RSS 缓存</strong>
                          <span>清空保存在本地的 RSS 订阅临时哈希与发布项缓存</span>
                        </div>
                        <el-button type="primary" plain @click="runAction('/cache/rss/clear')">立即清除</el-button>
                      </div>
                      <div class="action-item-row">
                        <div class="action-desc">
                          <strong>清除过期缓存</strong>
                          <span>自动检索并清理已经失效或长时间未更新的系统缓存</span>
                        </div>
                        <el-button type="primary" plain @click="runAction('/cache/expired/clear')">立即清理</el-button>
                      </div>
                      <div class="action-item-row warning-border">
                        <div class="action-desc">
                          <strong>清空全部处理缓存</strong>
                          <span>强力清除包括作品元数据、海报、索引在内的所有临时缓存</span>
                        </div>
                        <el-popconfirm title="会清空全部处理缓存，包括元数据和匹配缓存。确定？" @confirm="runAction('/cache/clear')">
                          <template #reference>
                            <el-button type="warning">彻底清空</el-button>
                          </template>
                        </el-popconfirm>
                      </div>
                    </div>
                  </div>

                  <!-- Group 2: Media Database Maintenance -->
                  <div class="maintenance-group-card">
                    <div class="group-header">
                      <h3>📦 契约与资源维护</h3>
                      <p>校验本地文件一致性，更新媒体库元数据索引</p>
                    </div>
                    <div class="group-body">
                      <div class="action-item-row">
                        <div class="action-desc">
                          <strong>刷新全部本地状态</strong>
                          <span>遍历检测本地已下载文件的物理存在状态，同步数据库标记</span>
                        </div>
                        <el-button type="primary" @click="refreshAllLocalStatus">执行刷新</el-button>
                      </div>
                      <div class="action-item-row">
                        <div class="action-desc">
                          <strong>刷新全部元数据</strong>
                          <span>从 Bangumi/TMDB 重新全量抓取并复核本地已收录的作品信息</span>
                        </div>
                        <el-popconfirm title="会按现有 Bangumi/TMDB ID 刷新所有条目元数据，并按设置校验 NFO。确定执行？" @confirm="refreshAllMetadata">
                          <template #reference>
                            <el-button type="primary">重抓元数</el-button>
                          </template>
                        </el-popconfirm>
                      </div>
                      <div class="action-item-row">
                        <div class="action-desc">
                          <strong>整理全部本地资源</strong>
                          <span>根据当前设置的命名规则，重新分类整理已识别的本地作品</span>
                        </div>
                        <el-popconfirm title="会把已绑定且存在的本地文件整理到当前命名规则路径，目标同名文件会被覆盖。确定执行？" @confirm="organizeAllLocalFiles">
                          <template #reference>
                            <el-button type="primary">整理归档</el-button>
                          </template>
                        </el-popconfirm>
                      </div>
                    </div>
                  </div>

                  <!-- Group 3: Migrations & Dangerous Resets -->
                  <div class="maintenance-group-card full-row-card">
                    <div class="group-header">
                      <h3>🛠️ 数据迁移与系统格式化</h3>
                      <p>执行底层数据表结构升级或彻底格式化系统记录（敏感操作）</p>
                    </div>
                    <div class="group-body flex-grid-body">
                      <div class="action-item-row">
                        <div class="action-desc">
                          <strong>迁移集数模型</strong>
                          <span>将原有作品下的集数条目迁移为单集单纪录的高级调度模型</span>
                        </div>
                        <el-popconfirm title="迁移前会自动备份数据库。确定把旧资源模型迁移为每集一条资源，并按纯作品名目录计算路径？" @confirm="migrateEpisodeModel">
                          <template #reference>
                            <el-button type="primary">运行迁移</el-button>
                          </template>
                        </el-popconfirm>
                      </div>
                      <div class="action-item-row">
                        <div class="action-desc">
                          <strong>修复为纯作品名路径</strong>
                          <span>把老版本的识别文件迁移至全新规划的作品独立层级文件夹中</span>
                        </div>
                        <el-popconfirm title="会把已识别到的旧本地文件移动到纯作品名目录，并同步修复数据库状态。确定执行？" @confirm="repairLocalPaths">
                          <template #reference>
                            <el-button type="primary">运行修复</el-button>
                          </template>
                        </el-popconfirm>
                      </div>
                      <div class="action-item-row warning-border">
                        <div class="action-desc">
                          <strong>清理无效集数</strong>
                          <span>自动扫描并清理破损、信息丢失或者无法成功关联的集数记录</span>
                        </div>
                        <el-popconfirm title="会清理无法识别集数的发布、资源、字幕和下载记录。确定执行？" @confirm="runAction('/maintenance/cleanup-invalid-episodes')">
                          <template #reference>
                            <el-button type="warning">清理无效</el-button>
                          </template>
                        </el-popconfirm>
                      </div>
                      <div class="action-item-row danger-border">
                        <div class="action-desc">
                          <strong>💥 擦除全部契约数据</strong>
                          <span>格式化并清空所有番剧、候选、任务、本地资源记录及历史日志</span>
                        </div>
                        <el-popconfirm title="会清空番剧、候选、任务、下载记录、本地资源记录和日志。确定？" @confirm="runAction('/system/clear-data')">
                          <template #reference>
                            <el-button type="danger">格式化系统</el-button>
                          </template>
                        </el-popconfirm>
                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
            <div class="form-actions"><el-button type="primary" size="large" :loading="savingSettings" @click="saveAllSettings">保存设置</el-button></div>
          </el-form>
        </el-card>
      </section>
</template>
