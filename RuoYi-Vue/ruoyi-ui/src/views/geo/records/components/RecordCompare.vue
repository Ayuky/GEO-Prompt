<template>
  <el-dialog
    title="评估记录对比"
    :visible.sync="dialogVisible"
    width="900px"
    top="5vh"
    append-to-body
    @close="handleClose"
  >
    <div v-if="records.length >= 2" class="compare-container">
      <!-- 对比柱状图 -->
      <el-card class="compare-section" shadow="never" title="评分对比">
        <div ref="compareChart" class="compare-chart" />
      </el-card>

      <!-- 对比表格 -->
      <el-card class="compare-section" shadow="never" title="详细对比">
        <el-table :data="compareTableData" border size="small" style="width: 100%">
          <el-table-column label="指标" prop="dimension" width="120" align="center" />
          <el-table-column
            v-for="(record, idx) in records"
            :key="idx"
            :label="`记录${record.id}`"
            align="center"
          >
            <template slot-scope="{ row }">
              <span :style="{ color: getScoreColor(row.values[idx]) }">
                {{ row.values[idx] !== '-' ? row.values[idx] : '-' }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 问答对比 -->
      <el-card class="compare-section" shadow="never" title="问答内容">
        <el-tabs>
          <el-tab-pane
            v-for="(record, idx) in records"
            :key="idx"
            :label="'记录' + record.id"
          >
            <div class="qa-block">
              <div class="qa-label">问题</div>
              <p class="qa-text">{{ record.question }}</p>
              <el-divider />
              <div class="qa-label">答案</div>
              <p class="qa-text">{{ record.answer }}</p>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
  </el-dialog>
</template>

<script>
import * as echarts from 'echarts'

const SCORE_DIMENSIONS = [
  { key: 'mention_rate', label: '提及率' },
  { key: 'naturalness_score', label: '自然度评分' },
  { key: 'context_match_score', label: '上下文匹配评分' },
  { key: 'sentiment_score', label: '情感评分' },
  { key: 'recommendation_score', label: '推荐评分' },
  { key: 'llm_judge_score', label: 'LLM评分' },
  { key: 'total_reward', label: '总奖励' }
]

const COLORS = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#b37feb']

export default {
  name: 'RecordCompare',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    records: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      chart: null
    }
  },
  computed: {
    dialogVisible: {
      get() {
        return this.visible
      },
      set(val) {
        this.$emit('update:visible', val)
      }
    },
    compareTableData() {
      return SCORE_DIMENSIONS.map(dim => ({
        dimension: dim.label,
        values: this.records.map(r => {
          const v = r[dim.key]
          return v !== null && v !== undefined ? this.formatScore(v) : '-'
        })
      }))
    },
    scoreScaleMax() {
      return 10
    }
  },
  watch: {
    visible(val) {
      if (val && this.records.length >= 2) {
        this._initTimer = setTimeout(() => this.initChart(), 200)
      }
    }
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
      }
      const el = this.$refs.compareChart
      if (!el) return
      this.chart = echarts.init(el)

      const dimensions = SCORE_DIMENSIONS.map(d => d.label)
      const series = this.records.map((record, idx) => ({
        name: '#' + record.id,
        type: 'bar',
        data: SCORE_DIMENSIONS.map(dim => record[dim.key] || 0),
        itemStyle: {
          color: COLORS[idx % COLORS.length]
        }
      }))

      this.chart.setOption({
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: this.records.map(r => '#' + r.id),
          bottom: 0
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: dimensions,
          axisLabel: {
            rotate: 20,
            fontSize: 11
          }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: this.scoreScaleMax
        },
        series
      })
    },
    formatScore(v) {
      const n = typeof v === 'number' ? v : parseFloat(v)
      if (isNaN(n)) return String(v)
      return this.scoreScaleMax > 1 ? n.toFixed(1) : n.toFixed(4)
    },
    getScoreColor(v) {
      if (v === '-') return '#909399'
      const num = parseFloat(v) / this.scoreScaleMax
      if (isNaN(num)) return '#909399'
      if (num < 0.3) return '#f56c6c'
      if (num < 0.6) return '#e6a23c'
      if (num < 0.8) return '#409eff'
      return '#67c23a'
    },
    handleClose() {
      if (this.chart) {
        this.chart.dispose()
        this.chart = null
      }
      this.$emit('update:visible', false)
    }
  }
}
</script>

<style scoped>
.compare-container {
  max-height: 70vh;
  overflow-y: auto;
}

.compare-section {
  margin-bottom: 16px;
}

.compare-chart {
  width: 100%;
  height: 350px;
}

.qa-block {
  padding: 8px 0;
}

.qa-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  margin-bottom: 6px;
}

.qa-text {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
</style>
