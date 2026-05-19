<template>
  <div class="score-bar-wrapper">
    <div class="score-label">
      <span>{{ label }}</span>
      <span class="score-value" :style="{ color: barColor }">{{ scoreText }}</span>
    </div>
    <div class="score-bar-track">
      <div
        class="score-bar-fill"
        :style="{ width: percentage + '%', backgroundColor: barColor }"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScoreBar',
  props: {
    label: {
      type: String,
      required: true
    },
    value: {
      type: Number,
      default: 0
    },
    max: {
      type: Number,
      default: 10
    }
  },
  computed: {
    ratio() {
      return this.value / this.max
    },
    percentage() {
      return Math.min(100, this.ratio * 100)
    },
    scoreText() {
      return this.value.toFixed(1)
    },
    barColor() {
      const v = this.ratio
      if (v < 0.3) return '#f56c6c'
      if (v < 0.6) return '#e6a23c'
      if (v < 0.8) return '#409eff'
      return '#67c23a'
    }
  }
}
</script>

<style scoped>
.score-bar-wrapper {
  margin-bottom: 12px;
}
.score-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
  color: #606266;
}
.score-value {
  font-weight: 600;
}
.score-bar-track {
  height: 8px;
  background-color: #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}
.score-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}
</style>
