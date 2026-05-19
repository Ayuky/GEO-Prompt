<template>
  <div :class="className" :style="{ height: height, width: width }" />
</template>

<script>
import * as echarts from 'echarts'
import resize from '@/views/dashboard/mixins/resize'

const SCORE_INDICATORS = [
  { name: '提及率', max: 10 },
  { name: '自然度评分', max: 10 },
  { name: '上下文匹配评分', max: 10 },
  { name: '情感评分', max: 10 },
  { name: '推荐评分', max: 10 },
  { name: 'LLM评分', max: 10 }
]

export default {
  name: 'ScoreRadar',
  mixins: [resize],
  props: {
    className: { type: String, default: 'chart' },
    width: { type: String, default: '100%' },
    height: { type: String, default: '320px' },
    recordData: { type: Object, required: true },
    options: { type: Object, default: () => ({}) }
  },
  data() {
    return { chart: null, _initTimer: null }
  },
  watch: {
    recordData: {
      deep: true,
      handler() {
        this.refreshChart()
      }
    }
  },
  mounted() {
    this.initChart()
  },
  beforeDestroy() {
    if (this._initTimer) {
      clearTimeout(this._initTimer)
      this._initTimer = null
    }
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  methods: {
    initChart() {
      if (this.chart) {
        this.chart.dispose()
        this.chart = null
      }
      // Wait for DOM to be ready; fallback to a short delay if container has no size yet
      this.$nextTick(() => {
        const el = this.$el
        if (!el || el.offsetWidth === 0 || el.offsetHeight === 0) {
          this._initTimer = setTimeout(() => this.initChart(), 100)
          return
        }
        this.chart = echarts.init(el)
        this.updateChart()
      })
    },
    refreshChart() {
      if (!this.chart) {
        this.initChart()
      } else {
        this.updateChart()
      }
    },
    updateChart() {
      if (!this.chart) return
      const record = this.recordData || {}
      const values = [
        record.mention_rate || 0,
        record.naturalness_score || 0,
        record.context_match_score || 0,
        record.sentiment_score || 0,
        record.recommendation_score || 0,
        record.llm_judge_score || 0
      ]

      this.chart.setOption({
        tooltip: { trigger: 'item' },
        radar: {
          indicator: SCORE_INDICATORS,
          radius: '65%',
          center: ['50%', '55%'],
          shape: 'polygon',
          name: {
            textStyle: { color: '#606266', fontSize: 12 }
          },
          splitArea: {
            areaStyle: {
              color: ['rgba(64,158,255,0.02)', 'rgba(64,158,255,0.05)']
            }
          }
        },
        series: [{
          type: 'radar',
          data: [{
            value: values,
            name: '评分维度',
            areaStyle: { color: 'rgba(64,158,255,0.2)' },
            lineStyle: { color: '#409eff', width: 2 },
            itemStyle: { color: '#409eff' }
          }]
        }]
      }, true)

      // Ensure chart fills its container after options are set
      this.chart.resize()
    }
  }
}
</script>
