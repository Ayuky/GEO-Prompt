<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never">
      <div slot="header">
        <el-button icon="el-icon-arrow-left" size="mini" @click="$router.back()">返回</el-button>
        <span style="margin-left: 12px; font-size: 18px; font-weight: 600;">{{ experiment.name }}</span>
        <el-tag :type="statusTagType(experiment.status)" size="small" style="margin-left: 12px;">
          {{ experiment.status }}
        </el-tag>
      </div>

      <!-- 收敛曲线 -->
      <el-row :gutter="20">
        <el-col :span="24">
          <div class="chart-header">
            <span class="chart-title">Prompt 训练演化收敛曲线</span>
            <el-tooltip content="展示各轮次的平均奖励和评判分数变化趋势，反映Prompt策略的收敛效果" placement="top">
              <i class="el-icon-info" style="color: #909399; cursor: help;" />
            </el-tooltip>
          </div>
          <div ref="chartRef" class="convergence-chart" />
        </el-col>
      </el-row>

      <!-- 实验概要 -->
      <el-row :gutter="20" style="margin-top: 24px;">
        <el-col :span="4">
          <div class="stat-card">
            <div class="stat-label">当前轮次</div>
            <div class="stat-value">{{ experiment.current_round }} / {{ experiment.max_rounds }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-card">
            <div class="stat-label">最佳奖励</div>
            <div class="stat-value highlight">{{ formatScore(experiment.best_reward) }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-card">
            <div class="stat-label">生成模型</div>
            <div class="stat-value small">{{ experiment.model_name || '-' }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-card">
            <div class="stat-label">评判模型</div>
            <div class="stat-value small">{{ experiment.judge_model_name || '-' }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-card">
            <div class="stat-label">生成模型 ID</div>
            <div class="stat-value small">{{ experiment.model_id }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-card">
            <div class="stat-label">创建时间</div>
            <div class="stat-value small">{{ formatTime(experiment.created_at) }}</div>
          </div>
        </el-col>
      </el-row>

      <!-- 版本历史表格 -->
      <el-divider content-position="left">版本演化历史</el-divider>
      <el-table :data="versions" border stripe size="small" style="margin-top: 16px;">
        <el-table-column label="轮次" align="center" prop="round_index" width="70" />
        <el-table-column label="生成策略" align="center" prop="generator_type" width="140">
          <template slot-scope="scope">
            <el-tag :type="genTypeTag(scope.row.generator_type)" size="mini">
              {{ genTypeLabel(scope.row.generator_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Prompt 内容" align="left" prop="prompt_text" min-width="300" :show-overflow-tooltip="true" />
        <el-table-column label="平均奖励" align="center" width="120">
          <template slot-scope="scope">
            <el-tag :type="rewardTagType(scope.row.mean_reward)" size="small">
              {{ formatScore(scope.row.mean_reward) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评判分数" align="center" width="120">
          <template slot-scope="scope">
            {{ formatScore(scope.row.mean_judge_score) }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" align="center" width="160">
          <template slot-scope="scope">
            {{ formatTime(scope.row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && versions.length === 0" description="暂无轮次数据，请先运行实验" />
    </el-card>
  </div>
</template>

<script>
import { getExperiment, getExperimentVersions } from '@/api/geo/experiments'
import * as echarts from 'echarts'

export default {
  name: 'GeopromptExperimentDetail',
  data() {
    return {
      loading: false,
      experiment: {
        id: null,
        name: '',
        status: '',
        model_id: null,
        model_name: '',
        judge_model_id: null,
        judge_model_name: '',
        current_round: 0,
        max_rounds: 0,
        best_reward: 0,
        created_at: null
      },
      versions: [],
      chart: null
    }
  },
  computed: {
    experimentId() {
      return this.$route.params.experimentId
    }
  },
  mounted() {
    this.loadData()
    window.addEventListener('resize', this.handleResize)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize)
    if (this.chart) {
      this.chart.dispose()
    }
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const [expRes, verRes] = await Promise.all([
          getExperiment(this.experimentId),
          getExperimentVersions(this.experimentId)
        ])
        this.experiment = expRes
        this.versions = Array.isArray(verRes) ? verRes : []
        this.$nextTick(() => this.renderChart())
      } catch (e) {
        this.$message.error('加载实验详情失败: ' + (e.message || '未知错误'))
      } finally {
        this.loading = false
      }
    },
    renderChart() {
      if (this.chart) this.chart.dispose()
      if (this.versions.length === 0) return

      const dom = this.$refs.chartRef
      if (!dom) return

      this.chart = echarts.init(dom, 'macarons')

      const rounds = this.versions.map(v => `R${v.round_index}`)
      const rewards = this.versions.map(v => Number(v.mean_reward?.toFixed(4)) || 0)
      const judgeScores = this.versions.map(v => Number(v.mean_judge_score?.toFixed(4)) || 0)
      const bestReward = Number(this.experiment.best_reward?.toFixed(4)) || 0

      const option = {
        title: {
          text: 'Prompt 策略收敛曲线',
          subtext: `共 ${this.versions.length} 轮 · 最佳奖励: ${bestReward}`,
          left: 'center',
          textStyle: { fontSize: 15, fontWeight: 'bold' },
          subtextStyle: { fontSize: 12, color: '#909399' }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross', crossStyle: { color: '#999' } },
          formatter: params => {
            let html = `<strong>${params[0].axisValue}</strong><br/>`
            params.forEach(p => {
              html += `${p.marker} ${p.seriesName}: <strong>${p.value}</strong><br/>`
            })
            return html
          }
        },
        legend: {
          data: ['平均奖励', '评判分数', '最佳奖励(参考线)'],
          bottom: 0
        },
        grid: {
          left: '3%',
          right: '5%',
          top: '18%',
          bottom: '12%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: rounds,
          name: '轮次',
          axisLabel: { rotate: rounds.length > 15 ? 45 : 0 }
        },
        yAxis: {
          type: 'value',
          name: '分值',
          min: 0,
          max: 10,
          interval: 2,
          axisLabel: { formatter: '{value}' }
        },
        series: [
          {
            name: '平均奖励',
            type: 'line',
            data: rewards,
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: { width: 3, color: '#409EFF' },
            itemStyle: { color: '#409EFF' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(64,158,255,0.25)' },
                { offset: 1, color: 'rgba(64,158,255,0.02)' }
              ])
            },
            markLine: bestReward > 0 ? {
              silent: true,
              data: [{ yAxis: bestReward, name: '最佳' }],
              lineStyle: { type: 'dashed', color: '#E6A23C' },
              label: { formatter: '最佳 {c}' }
            } : undefined
          },
          {
            name: '评判分数',
            type: 'line',
            data: judgeScores,
            smooth: true,
            symbol: 'diamond',
            symbolSize: 8,
            lineStyle: { width: 2.5, color: '#67C23A', type: 'dashed' },
            itemStyle: { color: '#67C23A' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(103,194,58,0.2)' },
                { offset: 1, color: 'rgba(103,194,58,0.02)' }
              ])
            }
          },
          {
            name: '最佳奖励(参考线)',
            type: 'line',
            data: [],
            markLine: bestReward > 0 ? {
              silent: true,
              symbol: 'none',
              data: [{ yAxis: bestReward, name: '最佳' }],
              lineStyle: { type: 'dashed', color: '#E6A23C', width: 1.5 },
              label: { formatter: '最佳 {c}' }
            } : undefined
          }
        ]
      }

      this.chart.setOption(option)
    },
    handleResize() {
      if (this.chart) this.chart.resize()
    },
    statusTagType(status) {
      const map = { created: 'info', running: '', finished: 'success', failed: 'danger' }
      return map[status] || 'info'
    },
    genTypeTag(type) {
      const map = { random: '', template_mutation: 'success', structured_template: 'warning' }
      return map[type] || 'info'
    },
    genTypeLabel(type) {
      const map = { random: '随机生成', template_mutation: '模板变异', structured_template: '结构模板' }
      return map[type] || type
    },
    rewardTagType(value) {
      if (value == null) return 'info'
      if (value < 0) return 'danger'
      if (value < 3) return 'warning'
      if (value < 6) return 'primary'
      return 'success'
    },
    formatScore(val) {
      if (val == null) return '-'
      return Number(val).toFixed(2)
    },
    formatTime(time) {
      if (!time) return '-'
      return new Date(time).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.convergence-chart {
  width: 100%;
  height: 420px;
  margin-top: 8px;
}

.chart-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.stat-card {
  text-align: center;
  padding: 16px 8px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.stat-value.highlight {
  color: #409EFF;
}

.stat-value.small {
  font-size: 14px;
  font-weight: 500;
}
</style>
