<template>
  <div class="app-container">
    <!-- 面包屑 -->
    <el-breadcrumb separator="/" style="margin-bottom: 16px">
      <el-breadcrumb-item :to="{ path: '/geo/langfuse' }">Langfuse 追踪</el-breadcrumb-item>
      <el-breadcrumb-item>追踪详情</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- Trace 基本信息 -->
    <el-card class="box-card" v-loading="loading">
      <div slot="header" class="clearfix">
        <span>追踪信息</span>
      </div>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="追踪ID">{{ trace.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ trace.name }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ trace.latency != null ? trace.latency + ' ms' : '-' }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ formatTime(trace.timestamp) }}</el-descriptions-item>
        <el-descriptions-item label="环境">{{ trace.environment || '-' }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ trace.version || trace.release || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Input" :span="2">
          <pre class="json-block">{{ formatJSON(trace.input) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="Output" :span="2">
          <pre class="json-block">{{ formatJSON(trace.output) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="Metadata" :span="2">
          <pre class="json-block">{{ formatJSON(trace.metadata) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Scores -->
    <el-card class="box-card" v-if="scores.length > 0">
      <div slot="header" class="clearfix">
        <span>评分 ({{ scores.length }})</span>
      </div>
      <el-table :data="scores" border size="small">
        <el-table-column label="名称" prop="name" width="180" />
        <el-table-column label="值" prop="value" width="120" />
        <el-table-column label="类型" prop="dataType" width="100" />
        <el-table-column label="来源" prop="source" width="100" />
        <el-table-column label="备注" prop="comment" min-width="200" show-overflow-tooltip />
        <el-table-column label="时间" width="180">
          <template slot-scope="scope">{{ formatTime(scope.row.timestamp) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Observations 树 -->
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>Observations ({{ observations.length }})</span>
      </div>
      <el-table
        :data="observations"
        border
        size="small"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        default-expand-all
      >
        <el-table-column label="名称" prop="name" min-width="200" show-overflow-tooltip />
        <el-table-column label="类型" width="100">
          <template slot-scope="scope">
            <el-tag :type="typeTagType(scope.row.type)" size="mini">{{ scope.row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="模型" prop="model" width="140" show-overflow-tooltip />
        <el-table-column label="耗时(ms)" width="100">
          <template slot-scope="scope">
            {{ scope.row.latency != null ? scope.row.latency : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="Token 用量" width="180">
          <template slot-scope="scope">
            <span v-if="scope.row.usage">
              {{ scope.row.usage.input || 0 }} + {{ scope.row.usage.output || 0 }}
              = {{ (scope.row.usage.input || 0) + (scope.row.usage.output || 0) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="费用" width="120">
          <template slot-scope="scope">
            <span v-if="scope.row.totalCost != null">${{ Number(scope.row.totalCost).toFixed(6) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="级别" width="80">
          <template slot-scope="scope">
            <el-tag v-if="scope.row.level" :type="levelTagType(scope.row.level)" size="mini">{{ scope.row.level }}</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { getTrace } from '@/api/geo/langfuse'

export default {
  name: 'LangfuseTraceDetail',
  data() {
    return {
      loading: true,
      trace: {},
      scores: [],
      observations: []
    }
  },
  created() {
    this.fetchTrace()
  },
  methods: {
    fetchTrace() {
      const traceId = this.$route.params.traceId
      if (!traceId) return
      this.loading = true
      getTrace(traceId).then(response => {
        const data = response.data || response
        this.trace = {
          id: data.id,
          name: data.name,
          latency: data.latency,
          timestamp: data.timestamp,
          environment: data.environment,
          version: data.version,
          release: data.release,
          input: data.input,
          output: data.output,
          metadata: data.metadata
        }
        this.scores = (data.scores || []).map(s => ({
          id: s.id, name: s.name, value: s.value, dataType: s.dataType,
          source: s.source, comment: s.comment, timestamp: s.timestamp
        }))
        this.observations = this.buildTree(data.observations || [])
        this.loading = false
      }).catch(() => {
        this.loading = false
      })
    },
    buildTree(observations) {
      const map = {}
      const roots = []
      observations.forEach(obs => {
        map[obs.id] = { ...obs, children: [] }
      })
      observations.forEach(obs => {
        if (obs.parentObservationId && map[obs.parentObservationId]) {
          map[obs.parentObservationId].children.push(map[obs.id])
        } else {
          roots.push(map[obs.id])
        }
      })
      return roots
    },
    formatTime(timestamp) {
      if (!timestamp) return '-'
      return new Date(timestamp).toLocaleString('zh-CN')
    },
    formatJSON(obj) {
      if (obj === null || obj === undefined) return '-'
      try {
        return JSON.stringify(obj, null, 2)
      } catch (e) {
        return String(obj)
      }
    },
    typeTagType(type) {
      return { GENERATION: 'success', SPAN: '', EVENT: 'info' }[type] || ''
    },
    levelTagType(level) {
      return { ERROR: 'danger', WARNING: 'warning', DEFAULT: 'info' }[level] || ''
    }
  }
}
</script>

<style scoped>
.box-card { margin-bottom: 16px; }
.json-block {
  margin: 0;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
