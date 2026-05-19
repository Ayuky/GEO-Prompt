<template>
  <div class="app-container">
    <!-- 指标概览卡片 -->
    <el-row :gutter="16" class="summary-row">
      <el-col :span="6">
        <div class="summary-card">
          <div class="summary-card__icon" style="background: rgba(64,158,255,0.1);">
            <i class="el-icon-document" style="color: #409eff;" />
          </div>
          <div class="summary-card__body">
            <div class="summary-card__label">Prompt总数</div>
            <div class="summary-card__value">{{ stats.total }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="summary-card">
          <div class="summary-card__icon" style="background: rgba(103,194,58,0.1);">
            <i class="el-icon-check" style="color: #67c23a;" />
          </div>
          <div class="summary-card__body">
            <div class="summary-card__label">平均提及率</div>
            <div class="summary-card__value">{{ summaryAvgMentionRate }}%</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="summary-card">
          <div class="summary-card__icon" style="background: rgba(230,162,60,0.1);">
            <i class="el-icon-trophy" style="color: #e6a23c;" />
          </div>
          <div class="summary-card__body">
            <div class="summary-card__label">平均奖励</div>
            <div class="summary-card__value">{{ summaryAvgReward }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="summary-card">
          <div class="summary-card__icon" style="background: rgba(144,147,153,0.1);">
            <i class="el-icon-s-data" style="color: #909399;" />
          </div>
          <div class="summary-card__body">
            <div class="summary-card__label">平均LLM评分</div>
            <div class="summary-card__value">{{ summaryAvgJudge }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 搜索区域 -->
    <el-card shadow="never" class="search-card">
      <el-form :model="queryParams" ref="queryForm" size="small" :inline="true" v-show="showSearch" label-width="72px">
        <el-form-item label="实验名称" prop="experimentId">
          <el-select
            v-model="queryParams.experimentId"
            placeholder="请选择实验"
            clearable
            filterable
            @change="handleQuery"
            style="width: 180px;"
          >
            <el-option
              v-for="exp in experimentOptions"
              :key="exp.id"
              :label="exp.name"
              :value="exp.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="轮次索引" prop="roundIndex">
          <el-input v-model="queryParams.roundIndex" placeholder="请输入" clearable @keyup.enter.native="handleQuery" style="width: 130px;" />
        </el-form-item>
        <el-form-item label="生成类型" prop="generatorType">
          <el-select v-model="queryParams.generatorType" placeholder="全部" clearable style="width: 140px;">
            <el-option label="随机生成" value="random" />
            <el-option label="模板变异" value="template_mutation" />
            <el-option label="策略驱动" value="policy" />
          </el-select>
        </el-form-item>
        <el-form-item label="策略动作" prop="policyAction">
          <el-input v-model="queryParams.policyAction" placeholder="请输入" clearable @keyup.enter.native="handleQuery" style="width: 130px;" />
        </el-form-item>
        <el-form-item label="创建时间" prop="createdAt">
          <el-date-picker clearable v-model="queryParams.createdAt" type="date" value-format="yyyy-MM-dd" placeholder="选择日期" style="width: 140px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
          <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作工具栏 -->
    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="danger" plain icon="el-icon-delete" size="mini" :disabled="multiple" @click="handleDelete" v-hasPermi="['geo:versions:remove']">删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="warning" plain icon="el-icon-download" size="mini" @click="handleExport" v-hasPermi="['geo:versions:export']">导出</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList" />
    </el-row>

    <!-- 数据表格 -->
    <el-table v-loading="loading" :data="versionsList" @selection-change="handleSelectionChange" row-key="id">
      <el-table-column type="selection" width="45" align="center" />
      <el-table-column label="ID" align="center" prop="id" width="60" />
      <el-table-column label="实验名称" align="center" prop="experiment_id" min-width="110" :show-overflow-tooltip="true">
        <template slot-scope="scope">
          {{ experimentMap[scope.row.experiment_id] || scope.row.experiment_id }}
        </template>
      </el-table-column>
      <el-table-column label="轮次" align="center" prop="round_index" width="60">
        <template slot-scope="scope">
          <el-tag size="mini" type="info" effect="plain">R{{ scope.row.round_index }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="生成器" align="center" prop="generator_type" width="120">
        <template slot-scope="scope">
          <el-tag :type="generatorTagType(scope.row.generator_type)" size="small" effect="dark">
            {{ generatorLabel(scope.row.generator_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Prompt文本" align="left" prop="prompt_text" min-width="220" :show-overflow-tooltip="true" />
      <el-table-column label="策略动作" align="center" width="100">
        <template slot-scope="scope">
          <el-tag v-if="scope.row.policy_action" :type="actionTagType(scope.row.policy_action)" size="small" effect="plain">
            {{ actionLabel(scope.row.policy_action) }}
          </el-tag>
          <span v-else style="color: #c0c4cc;">-</span>
        </template>
      </el-table-column>
      <el-table-column label="平均奖励" align="center" width="110">
        <template slot-scope="scope">
          <el-tag :type="rewardTagType(scope.row.mean_reward)" size="small" effect="dark">
            {{ scope.row.mean_reward != null ? Number(scope.row.mean_reward).toFixed(4) : '-' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="提及率" align="center" width="155">
        <template slot-scope="scope">
          <div class="inline-rate">
            <div class="inline-rate__bar">
              <div
                class="inline-rate__fill"
                :style="{ width: ((scope.row.prompt_mention_rate || 0) * 100) + '%', background: rateColor(scope.row.prompt_mention_rate) }"
              />
            </div>
            <span class="inline-rate__text" :style="{ color: rateColor(scope.row.prompt_mention_rate) }">
              {{ ((scope.row.prompt_mention_rate || 0) * 100).toFixed(1) }}%
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="LLM评分" align="center" prop="mean_judge_score" width="90">
        <template slot-scope="scope">
          <span :style="{ color: scoreColor(scope.row.mean_judge_score), fontWeight: 600 }">
            {{ scope.row.mean_judge_score != null ? Number(scope.row.mean_judge_score).toFixed(2) : '-' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" align="center" width="110">
        <template slot-scope="scope">
          <span style="font-size: 12px;">{{ parseTime(scope.row.created_at, '{y}-{m}-{d} {h}:{i}') }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="80" fixed="right">
        <template slot-scope="scope">
          <el-button size="mini" type="text" icon="el-icon-delete" style="color: #f56c6c;" @click="handleDelete(scope.row)" v-hasPermi="['geo:versions:remove']">删除</el-button>
        </template>
      </el-table-column>

      <!-- 展开行：详细信息 -->
      <el-table-column type="expand" width="40">
        <template slot-scope="{ row }">
          <div class="expanded-detail">
            <div class="expanded-section">
              <h4 class="expanded-section__title">
                <i class="el-icon-document" /> 完整Prompt
              </h4>
              <div class="expanded-prompt">{{ row.prompt_text }}</div>
            </div>
            <el-divider />
            <div class="expanded-section">
              <h4 class="expanded-section__title">
                <i class="el-icon-data-analysis" /> 指标详情
              </h4>
              <el-row :gutter="24">
                <el-col :span="8">
                  <score-bar label="Prompt提及率" :value="row.prompt_mention_rate || 0" />
                </el-col>
                <el-col :span="8">
                  <score-bar label="平均奖励" :value="normalizeReward(row.mean_reward)" :max="1.0" />
                </el-col>
                <el-col :span="8">
                  <score-bar label="平均LLM评分" :value="normalizeScore(row.mean_judge_score)" :max="10" />
                </el-col>
              </el-row>
            </div>
            <div v-if="row.metadata_json" class="expanded-meta">
              <el-tag size="mini" type="info">元数据: {{ row.metadata_json }}</el-tag>
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
  </div>
</template>

<script>
import { listVersions, delVersions, getVersionsStats } from "@/api/geo/versions"
import { listExperiments } from "@/api/geo/experiments"
import { exportToCSV, fetchAllPages } from "@/utils/export"
import ScoreBar from "@/views/geo/records/components/ScoreBar"

export default {
  name: "Versions",
  components: {
    ScoreBar
  },
  data() {
    return {
      loading: true,
      ids: [],
      single: true,
      multiple: true,
      showSearch: true,
      total: 0,
      versionsList: [],
      stats: {
        total: 0,
        avg_mention_rate: 0,
        avg_reward: 0,
        avg_judge_score: 0
      },
      experimentMap: {},
      experimentOptions: [],
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        experimentId: null,
        roundIndex: null,
        generatorType: null,
        promptText: null,
        policyAction: null,
        meanReward: null,
        meanJudgeScore: null,
        createdAt: null,
        updatedAt: null
      },
    }
  },
  computed: {
    summaryAvgMentionRate() {
      return (this.stats.avg_mention_rate * 100).toFixed(1)
    },
    summaryAvgReward() {
      return Number(this.stats.avg_reward || 0).toFixed(4)
    },
    summaryAvgJudge() {
      return Number(this.stats.avg_judge_score || 0).toFixed(2)
    }
  },
  created() {
    this.loadExperiments()
    this.getList()
    this.getStats()
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
      listVersions(this.queryParams).then(response => {
        if (response && response.items) {
          this.versionsList = response.items
          this.total = response.total
        } else if (Array.isArray(response)) {
          this.versionsList = response
          this.total = response.length
        } else {
          this.versionsList = []
          this.total = 0
        }
        this.loading = false
      })
    },
    getStats() {
      getVersionsStats().then(payload => {
        if (payload) {
          this.stats = {
            total: payload.total || 0,
            avg_mention_rate: payload.avg_mention_rate || 0,
            avg_reward: payload.avg_reward || 0,
            avg_judge_score: payload.avg_judge_score || 0
          }
        }
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
      this.$modal.confirm('是否确认删除提示词版本编号为"' + ids + '"的数据项？').then(function() {
        return delVersions(ids)
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
        const items = await fetchAllPages(p => listVersions({ ...params, ...p }))
        const headers = [
          'ID', '实验名称', '轮次', '生成器', 'Prompt文本',
          '策略动作', '平均奖励', '提及率', 'LLM评分', '创建时间'
        ]
        const genLabel = (t) => {
          const map = { random: '随机生成', template_mutation: '模板变异', structured_template: '结构模板' }
          return map[t] || t || ''
        }
        const expMap = this.experimentMap
        const rows = items.map(r => ({
          'ID': r.id,
          '实验名称': expMap[r.experiment_id] || r.experiment_id || '',
          '轮次': r.round_index != null ? `R${r.round_index}` : '',
          '生成器': genLabel(r.generator_type),
          'Prompt文本': r.prompt_text || '',
          '策略动作': r.policy_action || '',
          '平均奖励': r.mean_reward != null ? Number(r.mean_reward).toFixed(4) : '',
          '提及率': r.prompt_mention_rate != null ? (r.prompt_mention_rate * 100).toFixed(1) + '%' : '',
          'LLM评分': r.mean_judge_score != null ? Number(r.mean_judge_score).toFixed(2) : '',
          '创建时间': r.created_at || ''
        }))
        exportToCSV(headers, rows, `geo_versions_${new Date().getTime()}.csv`)
        this.$modal.msgSuccess(`成功导出 ${rows.length} 条记录`)
      } catch {
        this.$modal.msgError('导出失败，请稍后重试')
      } finally {
        loading.close()
      }
    },

    generatorLabel(type) {
      const map = { random: '随机生成', template_mutation: '模板变异', structured_template: '结构模板' }
      return map[type] || type || '-'
    },
    generatorTagType(type) {
      const map = { random: 'info', template_mutation: 'warning', structured_template: 'success' }
      return map[type] || 'info'
    },
    actionLabel(type) {
      const map = { random: '随机生成', template_mutation: '模板变异', structured_template: '结构模板' }
      return map[type] || type
    },
    actionTagType(type) {
      const map = { random: 'info', template_mutation: 'warning', structured_template: 'success' }
      return map[type] || 'info'
    },
    rateColor(val) {
      if (!val) return '#c0c4cc'
      if (val < 0.3) return '#f56c6c'
      if (val < 0.6) return '#e6a23c'
      if (val < 0.8) return '#409eff'
      return '#67c23a'
    },
    rewardTagType(val) {
      if (val == null) return 'info'
      const v = Number(val)
      if (v < 0) return 'danger'
      if (v < 0.3) return 'warning'
      if (v < 0.6) return ''
      return 'success'
    },
    scoreColor(val) {
      if (val == null) return '#c0c4cc'
      if (val < 3) return '#f56c6c'
      if (val < 6) return '#e6a23c'
      if (val < 8) return '#409eff'
      return '#67c23a'
    },
    normalizeReward(val) {
      const v = Number(val)
      return isNaN(v) ? 0 : Math.max(0, Math.min(1, v))
    },
    normalizeScore(val) {
      const v = Number(val)
      return isNaN(v) ? 0 : v
    }
  }
}
</script>

<style scoped>
/* 概览卡片 */
.summary-row {
  margin-bottom: 16px;
}

.summary-card {
  display: flex;
  align-items: center;
  padding: 18px 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.summary-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  margin-right: 14px;
  flex-shrink: 0;
}

.summary-card__body {
  flex: 1;
  min-width: 0;
}

.summary-card__label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.summary-card__value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
}

/* 搜索卡片 */
.search-card {
  margin-bottom: 16px;
}

.search-card >>> .el-card__body {
  padding: 16px 20px 0;
}

/* 表格内联提及率条 */
.inline-rate {
  display: flex;
  align-items: center;
  gap: 6px;
}

.inline-rate__bar {
  flex: 1;
  height: 6px;
  background: #ebeef5;
  border-radius: 3px;
  overflow: hidden;
}

.inline-rate__fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.inline-rate__text {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  min-width: 42px;
  text-align: right;
}

/* 展开行 */
.expanded-detail {
  padding: 16px 24px 20px;
}

.expanded-section {
  margin-bottom: 8px;
}

.expanded-section__title {
  font-size: 14px;
  color: #303133;
  margin: 0 0 12px 0;
  font-weight: 600;
}

.expanded-section__title i {
  margin-right: 6px;
  color: #409eff;
}

.expanded-prompt {
  background: #f8f9fb;
  border: 1px solid #e8eaed;
  border-radius: 6px;
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.7;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

.expanded-meta {
  margin-top: 12px;
}

/* 对话框 */
.dialog-footer {
  text-align: right;
}

/* 表格微调 */
.el-table >>> .el-table__expanded-cell {
  padding: 0;
  background: #fafbfc;
}
</style>
