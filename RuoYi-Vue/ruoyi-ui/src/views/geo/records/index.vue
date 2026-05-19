<template>
  <div class="app-container">
    <!-- 搜索区域 -->
    <el-form :model="queryParams" ref="queryForm" size="small" :inline="true" v-show="showSearch" label-width="80px">
      <el-form-item label="关键字" prop="keyword">
        <el-input
          v-model="queryParams.keyword"
          placeholder="搜索问题/答案"
          clearable
          @keyup.enter.native="handleQuery"
          style="width: 180px"
        />
      </el-form-item>
      <el-form-item label="实验名称" prop="experimentId">
        <el-select
          v-model="queryParams.experimentId"
          placeholder="请选择实验"
          clearable
          filterable
          @change="handleQuery"
          style="width: 180px"
        >
          <el-option
            v-for="exp in experimentOptions"
            :key="exp.id"
            :label="exp.name"
            :value="exp.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="Prompt ID" prop="promptVersionId">
        <el-input
          v-model="queryParams.promptVersionId"
          placeholder="Prompt ID"
          clearable
          @keyup.enter.native="handleQuery"
          style="width: 120px"
        />
      </el-form-item>
      <el-form-item label="总奖励">
        <el-input
          v-model="queryParams.totalRewardMin"
          placeholder="最小"
          clearable
          @keyup.enter.native="handleQuery"
          style="width: 90px"
        />
        <span style="margin: 0 6px; color: #c0c4cc;">-</span>
        <el-input
          v-model="queryParams.totalRewardMax"
          placeholder="最大"
          clearable
          @keyup.enter.native="handleQuery"
          style="width: 90px"
        />
      </el-form-item>
      
      <el-form-item label="创建时间" prop="createdAt">
        <el-date-picker
          v-model="queryParams.createdAt"
          type="date"
          value-format="yyyy-MM-dd"
          placeholder="选择日期"
          clearable
          style="width: 140px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- 统计面板 -->
    <records-stats-panel />

    <!-- 操作按钮 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="el-icon-delete"
          size="mini"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['geo:records:remove']"
        >删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="warning"
          plain
          icon="el-icon-download"
          size="mini"
          @click="handleExport"
          v-hasPermi="['geo:records:export']"
        >导出</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="info"
          plain
          icon="el-icon-view"
          size="mini"
          :disabled="single"
          @click="handleDetail"
        >详情</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="el-icon-sort"
          size="mini"
          :disabled="multiple || ids.length < 2"
          @click="handleCompare"
        >对比</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="recordsList"
      @selection-change="handleSelectionChange"
      row-key="id"
    >
      <el-table-column type="selection" width="45" align="center" />
      <el-table-column label="ID" align="center" prop="id" width="70" />
      <el-table-column label="实验名称" align="center" prop="experiment_id" width="120" :show-overflow-tooltip="true">
        <template slot-scope="scope">
          {{ experimentMap[scope.row.experiment_id] || scope.row.experiment_id }}
        </template>
      </el-table-column>
      <el-table-column label="关联PromptID" align="center" prop="prompt_version_id" width="110" />
      <el-table-column label="问题" align="left" prop="question" min-width="180" :show-overflow-tooltip="true" />
      <el-table-column label="LLM回答" align="left" prop="answer" min-width="180" :show-overflow-tooltip="true" />
      <el-table-column label="总奖励" align="center" width="100">
        <template slot-scope="scope">
          <el-tag :type="rewardTagType(scope.row.total_reward)" size="small">
            {{ scope.row.total_reward }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="延迟(ms)" align="center" prop="latency_ms" width="80" />
      <el-table-column label="创建时间" align="center" prop="created_at" width="100">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.created_at, '{y}-{m}-{d}') }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="130" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button size="mini" type="text" icon="el-icon-view" @click="handleDetail(scope.row)">详情</el-button>
          <el-button size="mini" type="text" icon="el-icon-delete" @click="handleDelete(scope.row)" v-hasPermi="['geo:records:remove']">删除</el-button>
        </template>
      </el-table-column>

      <!-- 展开行：详细评分 -->
      <el-table-column type="expand" width="1">
        <template slot-scope="{ row }">
          <div class="expanded-detail">
            <div class="expanded-scores">
              <div class="score-column">
                <score-bar label="提及率" :value="row.mention_rate || 0" />
                <score-bar label="自然度评分" :value="row.naturalness_score || 0" />
                <score-bar label="上下文匹配评分" :value="row.context_match_score || 0" />
              </div>
              <div class="score-column">
                <score-bar label="情感评分" :value="row.sentiment_score || 0" />
                <score-bar label="推荐评分" :value="row.recommendation_score || 0" />
                <score-bar label="LLM评分" :value="row.llm_judge_score || 0" />
              </div>
            </div>
            <el-divider content-position="left">答案</el-divider>
            <p class="expanded-answer">{{ row.answer }}</p>
            <div v-if="row.trace_id || row.raw_metrics_json" class="expanded-meta">
              <el-tag v-if="row.trace_id" size="mini" type="info" style="margin-right: 8px;">
                Trace: {{ row.trace_id }}
              </el-tag>
              <el-tag v-if="row.raw_metrics_json" size="mini" type="warning">
                含原始指标
              </el-tag>
            </div>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      :page.sync="queryParams.pageNum"
      :limit.sync="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 详情弹窗 -->
    <record-detail
      :visible.sync="detailVisible"
      :record="detailRecord"
    />

    <!-- 对比弹窗 -->
    <record-compare
      :visible.sync="compareVisible"
      :records="compareRecords"
    />
  </div>
</template>

<script>
import { listRecords, getRecords, delRecords } from "@/api/geo/records"
import { listExperiments } from "@/api/geo/experiments"
import { exportToCSV, fetchAllPages } from "@/utils/export"
import ScoreBar from './components/ScoreBar'
import RecordDetail from './components/RecordDetail'
import RecordCompare from './components/RecordCompare'
import RecordsStatsPanel from './components/RecordsStatsPanel'

export default {
  name: "Records",
  components: {
    ScoreBar,
    RecordDetail,
    RecordCompare,
    RecordsStatsPanel
  },
  data() {
    return {
      loading: true,
      ids: [],
      single: true,
      multiple: true,
      showSearch: true,
      total: 0,
      recordsList: [],
      detailVisible: false,
      detailRecord: {},
      compareVisible: false,
      compareRecords: [],
      experimentMap: {},
      experimentOptions: [],
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        keyword: null,
        experimentId: null,
        promptVersionId: null,
        totalRewardMin: null,
        totalRewardMax: null,
        createdAt: null
      }
    }
  },
  created() {
    this.loadExperiments()
    this.getList()
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
    getList() {
      this.loading = true
      // 清除空字符串字段，避免后端类型转换异常
      const params = { ...this.queryParams }
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null) {
          delete params[key]
        }
      })
      listRecords(params).then(response => {
        if (response && response.items) {
          this.recordsList = response.items
          this.total = response.total
        } else if (Array.isArray(response)) {
          this.recordsList = response
          this.total = response.length
        } else {
          this.recordsList = []
          this.total = 0
        }
        this.loading = false
      })
    },
    handleQuery() {
      this.queryParams.pageNum = 1
      this.getList()
    },
    resetQuery() {
      this.resetForm("queryForm")
      this.handleQuery()
    },
    handleSelectionChange(selection) {
      this.ids = selection.map(item => item.id)
      this.single = selection.length !== 1
      this.multiple = !selection.length
    },
    handleDelete(row) {
      const ids = row.id || this.ids
      this.$modal.confirm('是否确认删除评估记录编号为"' + ids + '"的数据项？').then(function() {
        return delRecords(ids)
      }).then(() => {
        this.getList()
        this.$modal.msgSuccess("删除成功")
      }).catch(() => {})
    },
    async handleExport() {
      const loading = this.$loading({ text: '正在导出数据，请稍候', spinner: 'el-icon-loading', background: 'rgba(0, 0, 0, 0.7)' })
      try {
        const params = { ...this.queryParams }
        delete params.pageNum
        delete params.pageSize
        Object.keys(params).forEach(key => {
          if (params[key] === '' || params[key] === null || params[key] === undefined) {
            delete params[key]
          }
        })
        const items = await fetchAllPages(p => listRecords({ ...params, ...p }))
        const headers = [
          'ID', '实验名称', '关联PromptID', '问题', 'LLM回答',
          '总奖励', '提及率', '自然度评分', '上下文匹配评分',
          '情感评分', '推荐评分', 'LLM评分', '延迟(ms)',
          '创建时间', 'Trace ID'
        ]
        const expMap = this.experimentMap
        const rows = items.map(r => ({
          'ID': r.id,
          '实验名称': expMap[r.experiment_id] || r.experiment_id || '',
          '关联PromptID': r.prompt_version_id != null ? r.prompt_version_id : '',
          '问题': r.question || '',
          'LLM回答': r.answer || '',
          '总奖励': r.total_reward != null ? r.total_reward : '',
          '提及率': r.mention_rate != null ? r.mention_rate : '',
          '自然度评分': r.naturalness_score != null ? r.naturalness_score : '',
          '上下文匹配评分': r.context_match_score != null ? r.context_match_score : '',
          '情感评分': r.sentiment_score != null ? r.sentiment_score : '',
          '推荐评分': r.recommendation_score != null ? r.recommendation_score : '',
          'LLM评分': r.llm_judge_score != null ? r.llm_judge_score : '',
          '延迟(ms)': r.latency_ms != null ? r.latency_ms : '',
          '创建时间': r.created_at || '',
          'Trace ID': r.trace_id || ''
        }))
        exportToCSV(headers, rows, `geo_records_${new Date().getTime()}.csv`)
        this.$modal.msgSuccess(`成功导出 ${rows.length} 条记录`)
      } catch {
        this.$modal.msgError('导出失败，请稍后重试')
      } finally {
        loading.close()
      }
    },

    /** 详情 */
    handleDetail(row) {
      const id = row.id || this.ids
      getRecords(id).then(response => {
        this.detailRecord = {
          ...response,
          experiment_name: this.experimentMap[response.experiment_id] || null
        }
        this.detailVisible = true
      })
    },

    /** 对比 */
    handleCompare() {
      if (this.ids.length < 2) {
        this.$modal.msgWarning('请至少选择两条记录进行对比')
        return
      }
      Promise.all(this.ids.map(id => getRecords(id))).then(responses => {
        this.compareRecords = responses
        this.compareVisible = true
      })
    },

    rewardTagType(value) {
      if (value === null || value === undefined) return 'info'
      if (value < 0) return 'danger'
      if (value < 0.3) return 'warning'
      if (value < 0.6) return 'primary'
      return 'success'
    }
  }
}
</script>

<style scoped>
.expanded-detail {
  padding: 16px 24px;
}

.expanded-scores {
  display: flex;
  gap: 48px;
}

.score-column {
  flex: 1;
  min-width: 0;
}

.expanded-answer {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.expanded-meta {
  margin-top: 12px;
}
</style>
