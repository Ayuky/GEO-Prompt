<template>
  <el-dialog
    :title="'第' + record.id + '条评估记录详情'"
    :visible.sync="dialogVisible"
    width="800px"
    top="5vh"
    append-to-body
    @opened="handleOpened"
    @close="handleClose"
  >
    <div v-if="record.id" class="detail-container">
      <!-- 汇总信息 -->
      <el-card class="detail-section" shadow="never">
        <div class="summary-grid">
          <div class="summary-item">
            <span class="summary-label">实验名称</span>
            <span class="summary-value">{{ record.experiment_name || record.experiment_id }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Prompt ID</span>
            <span class="summary-value">{{ record.prompt_version_id }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">总奖励</span>
            <el-tag :type="rewardTagType" size="small">{{ record.total_reward }}</el-tag>
          </div>
          <div class="summary-item">
            <span class="summary-label">延迟</span>
            <span class="summary-value">{{ record.latency_ms }} ms</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Trace ID</span>
            <span class="summary-value text-mono">{{ record.trace_id || '-' }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">创建时间</span>
            <span class="summary-value">{{ parseTime(record.created_at) }}</span>
          </div>
        </div>
      </el-card>

      <!-- 雷达图 -->
      <el-card class="detail-section" shadow="never" title="评分概览">
        <score-radar ref="radar" :record-data="record" height="300px" />
      </el-card>

      <!-- 评分详情 -->
      <el-card class="detail-section" shadow="never" title="评分详情">
        <score-bar label="提及率" :value="record.mention_rate || 0" />
        <score-bar label="自然度评分" :value="record.naturalness_score || 0" />
        <score-bar label="上下文匹配评分" :value="record.context_match_score || 0" />
        <score-bar label="情感评分" :value="record.sentiment_score || 0" />
        <score-bar label="推荐评分" :value="record.recommendation_score || 0" />
        <score-bar label="LLM评分" :value="record.llm_judge_score || 0" />
        <score-bar label="总奖励" :value="record.total_reward || 0" />
      </el-card>

      <!-- 问答内容 -->
      <el-card class="detail-section" shadow="never" title="问答内容">
        <div class="qa-block">
          <div class="qa-item">
            <div class="qa-label">问题</div>
            <div class="qa-content">{{ record.question }}</div>
          </div>
          <el-divider />
          <div class="qa-item">
            <div class="qa-label">答案</div>
            <div class="qa-content">{{ record.answer }}</div>
          </div>
        </div>
      </el-card>

      <!-- 原始指标 JSON -->
      <el-card v-if="record.raw_metrics_json" class="detail-section" shadow="never" title="原始指标">
        <pre class="json-block">{{ formatJson(record.raw_metrics_json) }}</pre>
      </el-card>
    </div>
  </el-dialog>
</template>

<script>
import ScoreBar from './ScoreBar'
import ScoreRadar from './ScoreRadar'
import { parseTime } from '@/utils/ruoyi'

export default {
  name: 'RecordDetail',
  components: {
    ScoreBar,
    ScoreRadar
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    record: {
      type: Object,
      default: () => ({})
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
    rewardTagType() {
      const v = this.record.total_reward
      if (v === null || v === undefined) return 'info'
      if (v < 0) return 'danger'
      if (v < 0.3) return 'warning'
      if (v < 0.6) return ''
      return 'success'
    }
  },
  methods: {
    parseTime(val) {
      return parseTime(val, '{y}-{m}-{d} {h}:{i}:{s}')
    },
    formatJson(str) {
      if (!str) return ''
      try {
        const obj = typeof str === 'string' ? JSON.parse(str) : str
        return JSON.stringify(obj, null, 2)
      } catch (e) {
        return str
      }
    },
    handleOpened() {
      const radar = this.$refs.radar
      if (radar) {
        radar.refreshChart()
      }
    },
    handleClose() {
      this.$emit('update:visible', false)
    }
  }
}
</script>

<style scoped>
.detail-container {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 12px;
  color: #909399;
}

.summary-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.text-mono {
  font-family: monospace;
  font-size: 12px;
}

.qa-block {
  padding: 4px 0;
}

.qa-item {
  margin-bottom: 8px;
}

.qa-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
  font-weight: 500;
}

.qa-content {
  font-size: 14px;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.json-block {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow: auto;
  margin: 0;
}
</style>
