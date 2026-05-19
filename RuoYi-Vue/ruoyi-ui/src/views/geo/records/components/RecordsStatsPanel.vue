<template>
  <div class="records-stats-panel">
    <!-- 汇总卡片 -->
    <el-row :gutter="16" class="summary-row">
      <el-col :span="6">
        <el-card shadow="never" class="summary-card">
          <div class="card-body">
            <div class="card-icon" style="background: #e6f7ff; color: #1890ff;">📊</div>
            <div class="card-info">
              <div class="card-value">{{ summaryData.totalCount || 0 }}</div>
              <div class="card-label">总记录数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="summary-card">
          <div class="card-body">
            <div class="card-icon" style="background: #fef0ef; color: #f56c6c;">⭐</div>
            <div class="card-info">
              <div class="card-value">{{ formatNum(summaryData.avgTotalReward) }}</div>
              <div class="card-label">平均总奖励</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="summary-card">
          <div class="card-body">
            <div class="card-icon" style="background: #e8f8e8; color: #67c23a;">⏱</div>
            <div class="card-info">
              <div class="card-value">{{ formatNum(summaryData.avgLatencyMs) }} ms</div>
              <div class="card-label">平均延迟</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="summary-card">
          <div class="card-body">
            <div class="card-icon" style="background: #f0f0ff; color: #722ed1;">🕐</div>
            <div class="card-info">
              <div class="card-value">{{ formatTime(summaryData.latestRecordAt) }}</div>
              <div class="card-label">最新记录</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" class="charts-row">
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <div slot="header"><span>评分分布</span></div>
          <div ref="pieChart" class="chart-container" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <div slot="header"><span>实验分组统计</span></div>
          <div ref="barChart" class="chart-container" />
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" class="charts-row">
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <div slot="header" class="chart-header-row">
            <span>Prompt趋势</span>
            <div class="chart-header-controls">
              <el-select
                v-model="selectedExperimentId"
                placeholder="选择实验"
                size="small"
                style="width: 140px"
                @change="onExperimentChange"
              >
                <el-option
                  v-for="exp in experimentOptions"
                  :key="exp.id"
                  :label="exp.name"
                  :value="exp.id"
                />
              </el-select>
              <el-select
                v-model="selectedMetric"
                placeholder="选择指标"
                size="small"
                style="width: 140px; margin-left: 8px"
                @change="onMetricChange"
              >
                <el-option
                  v-for="m in metricOptions"
                  :key="m.value"
                  :label="m.label"
                  :value="m.value"
                />
              </el-select>
            </div>
          </div>
          <div ref="promptTrendChart" class="chart-container" />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never" class="chart-card">
          <div slot="header"><span>评分维度均值</span></div>
          <div ref="radarBarChart" class="chart-container" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { debounce } from '@/utils'
import { getRecordsSummary, getRecordsStats } from "@/api/geo/records"

const PIE_COLORS = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a', '#909399', '#b37feb', '#fa8c16']

export default {
  name: 'RecordsStatsPanel',
  data() {
    return {
      summaryData: {},
      chartInstances: [],
      loading: false,
      experimentOptions: [],
      metricOptions: [
        { label: '综合奖励', value: 'total_reward' },
        { label: '提及率', value: 'mention_rate' },
        { label: '自然度评分', value: 'naturalness_score' },
        { label: '上下文匹配评分', value: 'context_match_score' },
        { label: '情感评分', value: 'sentiment_score' },
        { label: '推荐评分', value: 'recommendation_score' },
        { label: 'LLM评分', value: 'llm_judge_score' }
      ],
      selectedExperimentId: null,
      selectedMetric: 'total_reward',
      promptTrendData: []
    }
  },
  mounted() {
    this.loadData()
    this.__resizeHandler = debounce(() => {
      this.chartInstances.forEach(c => c && c.resize())
    }, 100)
    window.addEventListener('resize', this.__resizeHandler)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.__resizeHandler)
    this.chartInstances.forEach(c => c && c.dispose())
    this.chartInstances = []
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const [summaryRes, scoresRes, experimentRes, radarRes] = await Promise.all([
          getRecordsSummary(),
          getRecordsStats({ statType: 'byScores' }),
          getRecordsStats({ statType: 'byExperiment' }),
          getRecordsStats({ statType: 'byScoreRadar' })
        ])

        this.summaryData = summaryRes || {}

        this.experimentOptions = (experimentRes || []).map(exp => ({
          id: exp.experiment_id,
          name: exp.name
        }))

        this.$nextTick(() => {
          this.renderPieChart(scoresRes)
          this.renderBarChart(experimentRes)
          this.renderRadarBarChart(radarRes)
        })

        if (this.experimentOptions.length > 0 && this.selectedExperimentId == null) {
          this.selectedExperimentId = this.experimentOptions[0].id
        }
        await this.fetchAndRenderPromptTrend()
      } catch (e) {
        console.error('加载统计面板失败:', e)
      } finally {
        this.loading = false
      }
    },

    renderPieChart(apiData) {
      const el = this.$refs.pieChart
      if (!el) return
      const data = Array.isArray(apiData) ? apiData : []
      const chart = echarts.init(el)
      this.chartInstances.push(chart)
      chart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: 0, data: data.map(d => d.name) },
        series: [{
          type: 'pie',
          radius: ['30%', '60%'],
          center: ['50%', '45%'],
          data: data.map((d, i) => ({
            name: d.name,
            value: d.value,
            itemStyle: { color: PIE_COLORS[i % PIE_COLORS.length] }
          })),
          label: { show: false },
          emphasis: {
            label: { show: true, fontSize: '14', fontWeight: 'bold' }
          }
        }]
      })
    },

    renderBarChart(apiData) {
      const el = this.$refs.barChart
      if (!el) return
      const data = Array.isArray(apiData) ? apiData : []
      const chart = echarts.init(el)
      this.chartInstances.push(chart)
      chart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.map(d => d.name),
          axisLabel: { rotate: 30, fontSize: 11 }
        },
        yAxis: { type: 'value' },
        series: [{
          type: 'bar',
          data: data.map(d => d.value),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#409eff' },
              { offset: 1, color: '#a0cfff' }
            ])
          }
        }]
      })
    },

    async fetchAndRenderPromptTrend() {
      if (this.selectedExperimentId == null || !this.selectedMetric) {
        return
      }
      try {
        const data = await getRecordsStats({
          statType: 'byPromptTrend',
          experimentId: this.selectedExperimentId,
          metric: this.selectedMetric
        })
        this.promptTrendData = Array.isArray(data) ? data : []
      } catch (e) {
        console.error('获取版本趋势数据失败:', e)
        this.promptTrendData = []
      }
      this.$nextTick(() => {
        this.renderPromptTrendChart()
      })
    },

    renderPromptTrendChart() {
      const el = this.$refs.promptTrendChart
      if (!el) return
      const data = this.promptTrendData

      if (this._promptTrendChartInstance) {
        this._promptTrendChartInstance.dispose()
        const idx = this.chartInstances.indexOf(this._promptTrendChartInstance)
        if (idx > -1) this.chartInstances.splice(idx, 1)
      }

      const chart = echarts.init(el)
      this._promptTrendChartInstance = chart
      this.chartInstances.push(chart)

      chart.setOption({
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const p = params[0]
            return `${p.name}<br/>平均分: ${p.value}<br/>记录数: ${data[p.dataIndex]?.count ?? '-'}`
          }
        },
        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.map(d => d.name),
          axisLabel: { rotate: 30, fontSize: 11 },
          name: 'Prompt ID',
          nameLocation: 'center',
          nameGap: 35
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 10,
          name: '平均分',
          interval: 2
        },
        series: [{
          type: 'line',
          data: data.map(d => d.value),
          smooth: true,
          lineStyle: { color: '#67c23a', width: 2 },
          itemStyle: { color: '#67c23a' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
              { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
            ])
          }
        }]
      })
    },

    renderRadarBarChart(apiData) {
      const el = this.$refs.radarBarChart
      if (!el) return
      const data = Array.isArray(apiData) ? apiData : []
      const chart = echarts.init(el)
      this.chartInstances.push(chart)
      chart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.map(d => d.name),
          axisLabel: { rotate: 20, fontSize: 11 }
        },
        yAxis: { type: 'value', min: 0, max: 10 },
        series: [{
          type: 'bar',
          data: data.map((d, i) => ({
            value: d.value,
            itemStyle: {
              color: PIE_COLORS[i % PIE_COLORS.length],
              borderRadius: [4, 4, 0, 0]
            }
          })),
          barWidth: '50%',
          label: {
            show: true,
            position: 'top',
            formatter: p => p.data.value.toFixed(2)
          }
        }]
      })
    },

    onExperimentChange() {
      this.fetchAndRenderPromptTrend()
    },

    onMetricChange() {
      this.fetchAndRenderPromptTrend()
    },

    formatNum(val) {
      if (val === null || val === undefined) return '-'
      return Number(val).toFixed(4)
    },

    formatTime(val) {
      if (!val) return '-'
      return val.substring(0, 10)
    }
  }
}
</script>

<style scoped>
.records-stats-panel {
  margin-bottom: 20px;
}

.summary-row {
  margin-bottom: 16px;
}

.summary-card {
  border-radius: 6px;
}

.summary-card .card-body {
  display: flex;
  align-items: center;
  gap: 14px;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.card-info {
  flex: 1;
  min-width: 0;
}

.card-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-label {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.charts-row {
  margin-bottom: 16px;
}

.chart-card {
  border-radius: 6px;
}

.chart-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.chart-header-controls {
  display: flex;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 280px;
}
</style>
