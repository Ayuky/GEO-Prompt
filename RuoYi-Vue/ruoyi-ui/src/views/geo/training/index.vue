<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>RL 训练管理</span>
      </div>

      <!-- 统计卡片 -->
      <el-row :gutter="20" style="margin-bottom: 20px">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">总计</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card stat-running">
            <div class="stat-value">{{ stats.running }}</div>
            <div class="stat-label">运行中</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card stat-finished">
            <div class="stat-value">{{ stats.finished }}</div>
            <div class="stat-label">已完成</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card stat-failed">
            <div class="stat-value">{{ stats.failed }}</div>
            <div class="stat-label">失败</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 搜索表单 -->
      <el-form :model="queryParams" ref="queryForm" size="small" :inline="true" label-width="80px">
        <el-form-item label="实验名称" prop="experiment_id">
          <el-select
            v-model="queryParams.experiment_id"
            placeholder="请选择实验"
            clearable
            filterable
            @change="handleQuery"
          >
            <el-option
              v-for="exp in experimentOptions"
              :key="exp.id"
              :label="exp.name"
              :value="exp.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="算法" prop="algorithm">
          <el-select v-model="queryParams.algorithm" placeholder="请选择" clearable>
            <el-option label="PPO" value="ppo" />
            <el-option label="DQN" value="dqn" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="queryParams.status" placeholder="请选择" clearable>
            <el-option label="排队中" value="queued" />
            <el-option label="运行中" value="running" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已完成" value="finished" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
          <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table v-loading="loading" :data="trainingList" border>
        <el-table-column label="ID" align="center" prop="id" width="80" />
        <el-table-column label="实验名称" align="center" prop="experiment_id" min-width="120" :show-overflow-tooltip="true">
          <template slot-scope="scope">
            {{ experimentMap[scope.row.experiment_id] || scope.row.experiment_id }}
          </template>
        </el-table-column>
        <el-table-column label="算法" align="center" prop="algorithm" width="100">
          <template slot-scope="scope">
            <el-tag :type="scope.row.algorithm === 'ppo' ? 'success' : 'warning'" size="small">
              {{ scope.row.algorithm.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" align="center" prop="status" width="100">
          <template slot-scope="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" align="center" min-width="180">
          <template slot-scope="scope">
            <el-progress
              :percentage="getProgress(scope.row)"
              :status="scope.row.status === 'failed' ? 'exception' : undefined"
              :stroke-width="16"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column label="最佳奖励" align="center" prop="best_reward" width="120">
          <template slot-scope="scope">
            {{ scope.row.best_reward != null ? scope.row.best_reward.toFixed(4) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="模型路径" align="center" prop="model_path" min-width="150" show-overflow-tooltip />
        <el-table-column label="创建时间" align="center" prop="created_at" width="180">
          <template slot-scope="scope">
            {{ parseTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="200" fixed="right">
          <template slot-scope="scope">
            <el-button
              size="mini"
              type="text"
              icon="el-icon-view"
              @click="handleViewDetail(scope.row)"
            >详情</el-button>
            <el-button
              v-if="scope.row.status === 'running'"
              size="mini" type="text" icon="el-icon-video-pause"
              style="color:#e6a23c"
              @click="handlePause(scope.row)">暂停</el-button>
            <el-button
              v-if="scope.row.status === 'paused'"
              size="mini" type="text" icon="el-icon-video-play"
              style="color:#67c23a"
              @click="handleResume(scope.row)">恢复</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <pagination
        v-show="total > 0"
        :total="total"
        :page.sync="queryParams.page"
        :limit.sync="queryParams.limit"
        @pagination="loadList"
      />
    </el-card>

    <!-- 训练演化详情对话框 -->
    <el-dialog
      title="训练演化路线"
      :visible.sync="detailDialogVisible"
      width="1400px"
      top="3vh"
      @opened="onDetailOpened"
      @closed="onDetailClosed"
    >
      <!-- 概要卡片 -->
      <el-row :gutter="16" style="margin-bottom: 16px;">
        <el-col :span="4">
          <div class="evol-stat-card">
            <div class="evol-stat-label">Run ID</div>
            <div class="evol-stat-value">{{ currentRun.id }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="evol-stat-card">
            <div class="evol-stat-label">算法</div>
            <div class="evol-stat-value">{{ currentRun.algorithm ? currentRun.algorithm.toUpperCase() : '-' }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="evol-stat-card">
            <div class="evol-stat-label">进度</div>
            <div class="evol-stat-value">{{ currentRun.current_timestep }}/{{ currentRun.total_timesteps }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="evol-stat-card">
            <div class="evol-stat-label">最佳奖励</div>
            <div class="evol-stat-value highlight">{{ formatNum(currentRun.best_reward) }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="evol-stat-card">
            <div class="evol-stat-label">数据点数</div>
            <div class="evol-stat-value">{{ metricsData.length }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="evol-stat-card">
            <div class="evol-stat-label">状态</div>
            <div class="evol-stat-value">
              <el-tag :type="getStatusType(currentRun.status)" size="small">
                {{ getStatusLabel(currentRun.status) }}
              </el-tag>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-tabs v-model="evolTab" type="border-card" @tab-click="onEvolTabClick">
        <!-- Tab 1: Reward 演化曲线 -->
        <el-tab-pane label="Reward 收敛" name="reward">
          <div ref="rewardChart" class="evol-chart" />
        </el-tab-pane>

        <!-- Tab 2: Loss 曲线 -->
        <el-tab-pane label="Loss 曲线" name="loss">
          <div ref="entropyLossChart" class="loss-chart" />
          <div ref="policyLossChart" class="loss-chart" />
          <div ref="valueLossChart" class="loss-chart" />
        </el-tab-pane>

        <!-- Tab 3: 动作选择演化 -->
        <el-tab-pane label="动作选择" name="action">
          <el-row :gutter="16">
            <el-col :span="16">
              <div ref="actionTimelineChart" class="evol-chart" />
            </el-col>
            <el-col :span="8">
              <div ref="actionPieChart" class="evol-chart" />
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- Tab 4: 超参数 -->
        <el-tab-pane label="超参数" name="params">
          <pre class="json-block">{{ formatJson(currentRun.hyper_params) }}</pre>
          <div v-if="currentRun.model_path" style="margin-top: 12px;">
            <el-tag type="success">模型路径: {{ currentRun.model_path }}</el-tag>
          </div>
        </el-tab-pane>
      </el-tabs>

      <div slot="footer" class="dialog-footer">
        <el-button type="warning" plain icon="el-icon-download" size="small" :disabled="metricsData.length === 0" @click="handleExportMetrics">导出指标CSV</el-button>
        <el-button @click="detailDialogVisible = false">关 闭</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { listTrainingRuns, pauseTraining, resumeTraining, getTrainingMetrics } from '@/api/geo/training'
import { listExperiments } from '@/api/geo/experiments'
import { exportToCSV } from '@/utils/export'
import * as echarts from 'echarts'

const ACTION_LABELS = { 0: '随机生成', 1: '模板变异', 2: '结构模板' }
const ACTION_COLORS = { 0: '#909399', 1: '#E6A23C', 2: '#409EFF' }

export default {
  name: 'GeopromptTraining',
  data() {
    return {
      loading: false,
      trainingList: [],
      total: 0,
      experimentMap: {},
      experimentOptions: [],
      queryParams: {
        page: 1,
        limit: 10,
        experiment_id: '',
        algorithm: '',
        status: ''
      },
      stats: {
        total: 0,
        running: 0,
        paused: 0,
        finished: 0,
        failed: 0
      },
      autoRefreshTimer: null,
      detailDialogVisible: false,
      currentRun: {},
      metricsData: [],
      evolTab: 'reward',
      charts: {}
    }
  },
  created() {
    this.loadExperiments()
    this.loadList()
    this.startAutoRefresh()
  },
  beforeDestroy() {
    this.stopAutoRefresh()
  },
  methods: {
    loadExperiments() {
      listExperiments({ skip: 0, limit: 100 }).then(response => {
        const list = Array.isArray(response) ? response : (response.items || [])
        const map = {}
        const options = []
        list.forEach(exp => {
          map[exp.id] = exp.name
          options.push({ id: exp.id, name: exp.name })
        })
        this.experimentMap = map
        this.experimentOptions = options
      }).catch(() => {})
    },
    loadList() {
      this.loading = true
      const params = {
        experiment_id: this.queryParams.experiment_id || undefined,
        algorithm: this.queryParams.algorithm || undefined,
        status: this.queryParams.status || undefined,
        skip: (this.queryParams.page - 1) * this.queryParams.limit,
        limit: this.queryParams.limit
      }
      listTrainingRuns(params).then(response => {
        const items = (response && response.items) ? response.items : []
        this.trainingList = items
        this.total = (response && response.total != null) ? response.total : items.length
        this.updateStats()
        this.loading = false
      }).catch(() => {
        this.loading = false
      })
    },
    updateStats() {
      const list = this.trainingList
      this.stats.total = list.length
      this.stats.running = list.filter(r => r.status === 'running').length
      this.stats.paused = list.filter(r => r.status === 'paused').length
      this.stats.finished = list.filter(r => r.status === 'finished').length
      this.stats.failed = list.filter(r => r.status === 'failed').length
    },
    handleQuery() {
      this.queryParams.page = 1
      this.loadList()
    },
    resetQuery() {
      this.resetForm('queryForm')
      this.handleQuery()
    },
    handlePause(row) {
      this.$modal.confirm(`确认暂停训练 Run #${row.id} ？`).then(() => {
        pauseTraining(row.id).then(() => {
          this.$modal.msgSuccess('训练已暂停')
          this.loadList()
        }).catch(() => {})
      }).catch(() => {})
    },
    handleResume(row) {
      this.$modal.confirm(`确认恢复训练 Run #${row.id} ？`).then(() => {
        resumeTraining(row.id).then(() => {
          this.$modal.msgSuccess('训练已恢复运行')
          this.loadList()
        }).catch(() => {})
      }).catch(() => {})
    },
    handleViewDetail(row) {
      this.currentRun = { ...row }
      this.metricsData = []
      this.evolTab = 'reward'
      this.detailDialogVisible = true
    },

    handleExportMetrics() {
      if (this.metricsData.length === 0) return
      const headers = [
        'timestep', 'reward', 'entropy_loss', 'policy_loss',
        'value_loss', 'action', 'action_label'
      ]
      const rows = this.metricsData.map(m => {
        const meta = m.metricsJson || {}
        const action = meta.action != null ? meta.action : -1
        return {
          'timestep': m.timestep,
          'reward': m.reward != null ? m.reward : '',
          'entropy_loss': m.entropyLoss != null ? m.entropyLoss : '',
          'policy_loss': m.policyLoss != null ? m.policyLoss : '',
          'value_loss': m.valueLoss != null ? m.valueLoss : '',
          'action': action !== -1 ? action : '',
          'action_label': ACTION_LABELS[action] || ''
        }
      })
      exportToCSV(headers, rows, `geo_training_${this.currentRun.id}_metrics.csv`)
      this.$modal.msgSuccess(`成功导出 ${rows.length} 条指标数据`)
    },

    // --------------- 图表渲染 ---------------
    onDetailOpened() {
      this.loadMetricsAndRender()
    },
    onDetailClosed() {
      Object.values(this.charts).forEach(c => c.dispose())
      this.charts = {}
    },
    loadMetricsAndRender() {
      getTrainingMetrics(this.currentRun.id).then(data => {
        this.metricsData = Array.isArray(data) ? data : []
        this.$nextTick(() => this.renderAllCharts())
      }).catch(() => {
        this.metricsData = []
      })
    },
    renderAllCharts() {
      if (this.metricsData.length === 0) return
      this.renderRewardChart()
      this.renderEntropyLossChart()
      this.renderPolicyLossChart()
      this.renderValueLossChart()
      this.renderActionTimelineChart()
      this.renderActionPieChart()
    },
    onEvolTabClick() {
      this.$nextTick(() => {
        Object.values(this.charts).forEach(c => { try { c.resize() } catch (_) { /* ignore */ } })
      })
    },
    resizeCharts() {
      Object.values(this.charts).forEach(c => c.resize())
    },

    // --- Reward 收敛曲线 ---
    renderRewardChart() {
      const dom = this.$refs.rewardChart
      if (!dom) return
      if (this.charts.reward) this.charts.reward.dispose()
      this.charts.reward = echarts.init(dom)
      const ts = this.metricsData.map(m => m.timestep)
      const rewards = this.metricsData.map(m => Number(m.reward || 0))
      const best = Math.max(...rewards, 0)

      this.charts.reward.setOption({
        title: { text: '奖励演化曲线', left: 'center' },
        tooltip: { trigger: 'axis' },
        grid: { left: '4%', right: '4%', top: '16%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', data: ts, name: 'Timestep' },
        yAxis: { type: 'value', name: 'Reward' },
        series: [{
          name: 'Reward', type: 'line', data: rewards, smooth: true,
          symbol: 'circle', symbolSize: 5,
          lineStyle: { width: 2.5, color: '#409EFF' },
          itemStyle: { color: '#409EFF' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64,158,255,0.3)' },
              { offset: 1, color: 'rgba(64,158,255,0.02)' }
            ])
          },
          markLine: best > 0 ? {
            silent: true,
            data: [{ yAxis: best, name: '最佳' }],
            lineStyle: { type: 'dashed', color: '#E6A23C' },
            label: { formatter: '最佳 {c}' }
          } : undefined
        }]
      })
    },

    // --- Entropy Loss 曲线 ---
    renderEntropyLossChart() {
      const dom = this.$refs.entropyLossChart
      if (!dom) return
      if (this.charts.entropyLoss) this.charts.entropyLoss.dispose()
      this.charts.entropyLoss = echarts.init(dom)
      const ts = this.metricsData.map(m => m.timestep)
      const data = this.metricsData.map(m => Number(m.entropyLoss || 0))

      this.charts.entropyLoss.setOption({
        title: { text: 'Entropy Loss', left: 'center' },
        tooltip: { trigger: 'axis' },
        grid: { left: '8%', right: '4%', top: '16%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', data: ts, name: 'Timestep' },
        yAxis: { type: 'value', name: 'Entropy Loss' },
        series: [{
          name: 'Entropy Loss', type: 'line', data, smooth: true,
          symbol: 'circle', symbolSize: 4,
          lineStyle: { width: 2, color: '#E6A23C' },
          itemStyle: { color: '#E6A23C' }
        }]
      })
    },

    // --- Policy Loss 曲线 ---
    renderPolicyLossChart() {
      const dom = this.$refs.policyLossChart
      if (!dom) return
      if (this.charts.policyLoss) this.charts.policyLoss.dispose()
      this.charts.policyLoss = echarts.init(dom)
      const ts = this.metricsData.map(m => m.timestep)
      const data = this.metricsData.map(m => Number(m.policyLoss || 0))

      this.charts.policyLoss.setOption({
        title: { text: 'Policy Loss', left: 'center' },
        tooltip: { trigger: 'axis' },
        grid: { left: '8%', right: '4%', top: '16%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', data: ts, name: 'Timestep' },
        yAxis: { type: 'value', name: 'Policy Loss' },
        series: [{
          name: 'Policy Loss', type: 'line', data, smooth: true,
          symbol: 'circle', symbolSize: 4,
          lineStyle: { width: 2, color: '#F56C6C' },
          itemStyle: { color: '#F56C6C' }
        }]
      })
    },

    // --- Value Loss 曲线 ---
    renderValueLossChart() {
      const dom = this.$refs.valueLossChart
      if (!dom) return
      if (this.charts.valueLoss) this.charts.valueLoss.dispose()
      this.charts.valueLoss = echarts.init(dom)
      const ts = this.metricsData.map(m => m.timestep)
      const data = this.metricsData.map(m => Number(m.valueLoss || 0))

      this.charts.valueLoss.setOption({
        title: { text: 'Value Loss', left: 'center' },
        tooltip: { trigger: 'axis' },
        grid: { left: '8%', right: '4%', top: '16%', bottom: '8%', containLabel: true },
        xAxis: { type: 'category', data: ts, name: 'Timestep' },
        yAxis: { type: 'value', name: 'Value Loss' },
        series: [{
          name: 'Value Loss', type: 'line', data, smooth: true,
          symbol: 'circle', symbolSize: 4,
          lineStyle: { width: 2, color: '#67C23A' },
          itemStyle: { color: '#67C23A' }
        }]
      })
    },

    // --- 动作选择时间线 ---
    renderActionTimelineChart() {
      const dom = this.$refs.actionTimelineChart
      if (!dom) return
      if (this.charts.actionTimeline) this.charts.actionTimeline.dispose()
      this.charts.actionTimeline = echarts.init(dom)
      const actions = this.metricsData.map(m => {
        const meta = m.metricsJson || {}
        return meta.action != null ? meta.action : -1
      })

      const seriesData = [0, 1, 2].map(act => ({
        name: ACTION_LABELS[act] || `Action ${act}`,
        type: 'scatter',
        data: actions
          .map((a, i) => a === act ? [this.metricsData[i].timestep, this.metricsData[i].reward] : null)
          .filter(Boolean),
        symbolSize: 8,
        color: ACTION_COLORS[act]
      }))

      this.charts.actionTimeline.setOption({
        title: { text: '动作选择散点 (X=timestep, Y=reward)', left: 'center' },
        tooltip: {
          trigger: 'item',
          formatter: p => `${p.seriesName}<br/>Timestep: ${p.value[0]}<br/>Reward: ${p.value[1].toFixed(4)}`
        },
        legend: { data: Object.values(ACTION_LABELS), bottom: 0 },
        grid: { left: '4%', right: '4%', top: '16%', bottom: '12%', containLabel: true },
        xAxis: { type: 'value', name: 'Timestep' },
        yAxis: { type: 'value', name: 'Reward' },
        series: seriesData
      })
    },

    // --- 动作累计占比饼图 ---
    renderActionPieChart() {
      const dom = this.$refs.actionPieChart
      if (!dom) return
      if (this.charts.actionPie) this.charts.actionPie.dispose()
      this.charts.actionPie = echarts.init(dom)
      const counts = { 0: 0, 1: 0, 2: 0 }
      this.metricsData.forEach(m => {
        const meta = m.metricsJson || {}
        const a = meta.action != null ? meta.action : -1
        if (a in counts) counts[a]++
      })
      const pieData = Object.entries(counts)
        .filter(([, c]) => c > 0)
        .map(([a, c]) => ({ name: ACTION_LABELS[a] || `Action ${a}`, value: c, itemStyle: { color: ACTION_COLORS[a] } }))

      this.charts.actionPie.setOption({
        title: { text: '动作累计分布', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{b}: {c} 次 ({d}%)' },
        series: [{
          type: 'pie', radius: ['40%', '70%'], center: ['50%', '55%'],
          data: pieData,
          label: { formatter: '{b}\n{d}%' },
          emphasis: { label: { fontSize: 16, fontWeight: 'bold' } }
        }]
      })
    },

    getProgress(row) {
      if (!row.total_timesteps || row.total_timesteps === 0) return 0
      return Math.round((row.current_timestep / row.total_timesteps) * 100)
    },
    getStatusType(status) {
      const typeMap = {
        queued: 'info', running: 'warning', paused: '',
        finished: 'success', failed: 'danger'
      }
      return typeMap[status] || ''
    },
    getStatusLabel(status) {
      const labelMap = {
        queued: '排队中', running: '运行中', paused: '已暂停',
        finished: '已完成', failed: '失败'
      }
      return labelMap[status] || status
    },
    parseTime(time) {
      if (!time) return '-'
      return new Date(time).toLocaleString('zh-CN')
    },
    formatJson(obj) {
      if (!obj || Object.keys(obj).length === 0) return '默认'
      return JSON.stringify(obj, null, 2)
    },
    formatNum(val) {
      if (val == null) return '-'
      return Number(val).toFixed(4)
    },
    startAutoRefresh() {
      this.stopAutoRefresh()
      this.autoRefreshTimer = setInterval(() => {
        const hasActive = this.trainingList.some(
          r => r.status === 'queued' || r.status === 'running' || r.status === 'paused'
        )
        if (hasActive) this.loadList()
      }, 5000)
    },
    stopAutoRefresh() {
      if (this.autoRefreshTimer) {
        clearInterval(this.autoRefreshTimer)
        this.autoRefreshTimer = null
      }
    },
    resetForm(formName) {
      if (this.$refs[formName]) {
        this.$refs[formName].resetFields()
      }
    }
  }
}
</script>

<style scoped>
.box-card {
  margin-bottom: 20px;
}
.stat-card {
  text-align: center;
  padding: 10px 0;
}
.stat-card .stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}
.stat-card .stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.stat-running .stat-value {
  color: #e6a23c;
}
.stat-finished .stat-value {
  color: #67c23a;
}
.stat-failed .stat-value {
  color: #f56c6c;
}

/* 演化详情 */
.evol-stat-card {
  text-align: center;
  padding: 12px 4px;
  background: #f5f7fa;
  border-radius: 8px;
}
.evol-stat-label {
  font-size: 11px;
  color: #909399;
  margin-bottom: 6px;
}
.evol-stat-value {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}
.evol-stat-value.highlight {
  color: #409EFF;
}
.evol-chart {
  width: 100%;
  height: 420px;
}
.loss-chart {
  width: 100%;
  height: 200px;
  margin-bottom: 8px;
}
.json-block {
  margin: 0;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}
</style>
