<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>GeoPrompt 实验管理</span>
        <el-button
          style="float: right; padding: 10px 10px;font-weight: bold; box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4); transition: all 0.3s;"
          type="primary"
          icon="el-icon-plus"
          size="medium"
          @click="handleCreate"
        >创建实验</el-button>
      </div>

      <el-form :model="queryParams" ref="queryForm" size="small" :inline="true" label-width="68px">
        <el-form-item label="实验名称" prop="name">
          <el-input v-model="queryParams.name" placeholder="请输入实验名称" clearable @keyup.enter.native="handleQuery" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
          <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="experimentList" border>
        <el-table-column label="ID" align="center" prop="id" width="80" />
        <el-table-column label="实验名称" align="center" prop="name" min-width="150" />
        <el-table-column label="状态" align="center" width="160">
          <template slot-scope="scope">
            <div v-if="scope.row.status === 'running'" style="text-align:center">
              <i class="el-icon-loading" style="color:#409EFF" />
              <span style="font-size:12px;color:#409EFF">运行中</span>
              <el-progress
                :percentage="scope.row.max_rounds ? Math.round(scope.row.current_round / scope.row.max_rounds * 100) : 0"
                :show-text="true"
                :stroke-width="6"
                style="margin-top:4px"
              />
            </div>
            <el-tag v-else :type="getStatusType(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="生成模型" align="center" min-width="180">
          <template slot-scope="scope">
            <span>{{ scope.row.model_name || '-' }}</span>
            <span v-if="scope.row.model_name" style="color:#909399;font-size:12px;display:block">
              ID: {{ scope.row.model_id }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="评分模型" align="center" min-width="180">
          <template slot-scope="scope">
            <span>{{ scope.row.judge_model_name || '-' }}</span>
            <span v-if="scope.row.judge_model_name" style="color:#909399;font-size:12px;display:block">
              ID: {{ scope.row.judge_model_id }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="目标实体" align="center" min-width="200">
          <template slot-scope="scope">
            <el-tag
              v-for="(entity, index) in scope.row.target_entities"
              :key="index"
              size="small"
              style="margin-right: 5px"
            >{{ entity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前轮次" align="center" prop="current_round" width="100" />
        <el-table-column label="最佳奖励" align="center" prop="best_reward" width="120">
          <template slot-scope="scope">
            {{ scope.row.best_reward != null ? scope.row.best_reward.toFixed(4) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" align="center" prop="created_at" width="180">
          <template slot-scope="scope">{{ parseTime(scope.row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="280" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" type="text" icon="el-icon-view" @click="handleView(scope.row)">查看</el-button>
            <el-button size="mini" type="text" icon="el-icon-video-play" @click="handleRun(scope.row)"
                       :disabled="scope.row.status === 'running' || scope.row.status === 'paused'">运行</el-button>
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
            <el-button size="mini" type="text" icon="el-icon-s-data" @click="handleTrain(scope.row)">训练</el-button>
            <el-button size="mini" type="text" icon="el-icon-delete" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <pagination
        v-show="total > 0"
        :total="total"
        :page.sync="queryParams.page"
        :limit.sync="queryParams.limit"
        @pagination="getList"
      />
    </el-card>

    <!-- 运行实验对话框 -->
    <el-dialog title="运行实验" :visible.sync="runDialogVisible" width="600px">
      <el-form :model="runForm" ref="runForm" label-width="120px">
        <el-form-item label="问题列表" required>
          <el-input
            type="textarea" v-model="runForm.questionsText" :rows="5"
            placeholder="每行一个问题"
          />
        </el-form-item>
        <el-form-item label="生成模式">
          <el-select v-model="runForm.generator_mode" placeholder="请选择">
            <el-option label="随机生成" value="random" />
            <el-option label="模板变异" value="template_mutation" />
            <el-option label="结构模板" value="policy" />
            <el-option label="手动编写" value="manual" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="runForm.generator_mode === 'template_mutation'" label="源Prompt">
          <el-input
            type="textarea" v-model="runForm.sourcePrompt" :rows="4"
            placeholder="作为模板变异的基础文本。留空则使用系统默认Prompt
                        你是一名专业的GEO内容优化专家，请输出自然、专业、可信、可读的详细回答。
                        请分析目标用户的真实需求和使用场景，全面覆盖核心信息点，
                        简洁地解释关键内容，避免堆砌冗余信息，
                        基于事实依据给出有说服力的推荐和可执行的建议。"
          />
        </el-form-item>
        <el-form-item v-if="runForm.generator_mode === 'manual'" label="人工Prompt" required>
          <el-input
            type="textarea" v-model="runForm.manualPrompt" :rows="6"
            placeholder="在此编写人工Prompt，将作为系统提示词与用户问题组合发送给模型。多个Prompt之间用独占一行的“---”分隔，每轮依次使用"
          />
          <span class="form-tip" style="color:#409EFF" v-if="manualPromptCount > 0">
            检测到 {{ manualPromptCount }} 个Prompt（分隔符 ---），将依次用于各轮实验
          </span>
        </el-form-item>
        <el-form-item label="运行轮数">
          <el-input-number v-model="runForm.num_rounds" :min="1" :max="100" :step="1" />
        </el-form-item>
        <el-form-item label="LLM评分器">
          <el-switch v-model="runForm.enable_llm_scorer" />
          <span class="form-tip">关闭后仅使用规则评分，不调用LLM Judge（加速进度）</span>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitRun">确定</el-button>
      </div>
    </el-dialog>

    <!-- 启动RL训练对话框 -->
    <el-dialog title="启动 RL 训练" :visible.sync="trainDialogVisible" width="650px">
      <el-form :model="trainForm" ref="trainForm" label-width="130px">
        <el-form-item label="算法" required>
          <el-select v-model="trainForm.algorithm" placeholder="请选择算法" style="width: 100%">
            <el-option label="PPO (推荐)" value="ppo" />
            <el-option label="DQN" value="dqn" />
          </el-select>
        </el-form-item>
        <el-form-item label="总训练步数" required>
          <el-input-number v-model="trainForm.total_timesteps" :min="1" :max="50000" :step="100" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="问题列表" required>
          <el-input type="textarea" v-model="trainForm.questionsText" :rows="5" placeholder="每行一个问题" />
        </el-form-item>
        <el-form-item label="LLM评分器">
          <el-switch v-model="trainForm.enable_llm_scorer" />
          <span class="form-tip">关闭后仅使用规则评分，不调用LLM Judge（加速训练）</span>
        </el-form-item>
        <el-divider content-position="left">RL 超参数 <span style="font-size:12px;color:#909399;font-weight:normal">（留空使用默认值）</span></el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="日志间隔">
              <el-input v-model="trainForm.hyper.log_every" placeholder="20" style="width:100%" />
              <div class="form-tip">每隔 N 步保存一次损失和奖励日志，默认 20</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学习率">
              <el-input v-model="trainForm.hyper.lr" :placeholder="trainForm.algorithm === 'dqn' ? '0.0001' : '0.0003'" style="width:100%" />
              <div class="form-tip">控制参数更新幅度，PPO 默认 3e-4，DQN 默认 1e-4</div>
            </el-form-item>
          </el-col>
        </el-row>
        <template v-if="trainForm.algorithm === 'ppo'">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="采样步数">
                <el-input v-model="trainForm.hyper.n_steps" placeholder="64" style="width:100%" />
                <div class="form-tip">每次策略更新前采集的交互步数，范围 16~2048，默认 64</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="批次大小">
                <el-input v-model="trainForm.hyper.batch_size" placeholder="64" style="width:100%" />
                <div class="form-tip">每次训练的样本批次大小，范围 8~512，默认 64</div>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="折扣因子">
                <el-input v-model="trainForm.hyper.gamma" placeholder="0.99" style="width:100%" />
                <div class="form-tip">未来奖励的衰减系数，范围 0.8~1.0，默认 0.99</div>
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        <template v-if="trainForm.algorithm === 'dqn'">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="缓冲大小 (buffer_size)">
                <el-input v-model="trainForm.hyper.buffer_size" placeholder="5000" style="width:100%" />
                <div class="form-tip">经验回放缓冲区容量，范围 1000~100000，默认 5000</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="批次大小 (batch_size)">
                <el-input v-model="trainForm.hyper.batch_size" placeholder="32" style="width:100%" />
                <div class="form-tip">每次训练的样本批次大小，范围 8~512，默认 32</div>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="折扣因子 (gamma)">
                <el-input v-model="trainForm.hyper.gamma" placeholder="0.99" style="width:100%" />
                <div class="form-tip">未来奖励的衰减系数，范围 0.8~1.0，默认 0.99</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="探索步数 (learning_starts)">
                <el-input v-model="trainForm.hyper.learning_starts" placeholder="64" style="width:100%" />
                <div class="form-tip">随机探索的初始步数（不训练仅收集经验），默认 64</div>
              </el-form-item>
            </el-col>
          </el-row>
        </template>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="trainDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTrain" :loading="trainSubmitting">
          {{ trainSubmitting ? '启动中...' : '启动训练' }}
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { listExperiments, runExperimentRound, deleteExperiment, getExperiment, pauseExperiment, resumeExperiment } from '@/api/geo/experiments'
import { startTraining } from '@/api/geo/training'

export default {
  name: 'GeopromptExperiments',
  data() {
    return {
      loading: true,
      experimentList: [],
      total: 0,
      queryParams: { page: 1, limit: 10, name: '' },
      runDialogVisible: false,
      runForm: { experimentId: null, questionsText: '', generator_mode: 'random', num_rounds: 1, manualPrompt: '', sourcePrompt: '', enable_llm_scorer: true },
      pollingTimers: {},
      trainDialogVisible: false,
      trainSubmitting: false,
      trainForm: {
        experimentId: null, algorithm: 'ppo', total_timesteps: 1000,
        questionsText: '',
        hyper: { log_every: '', n_steps: '', batch_size: '', lr: '', gamma: '', buffer_size: '', learning_starts: '' },
        enable_llm_scorer: true
      }
    }
  },
  computed: {
    manualPromptCount() {
      if (!this.runForm.manualPrompt || !this.runForm.manualPrompt.trim()) return 0
      return this.runForm.manualPrompt.split(/\n---\r?\n|\r\n---\n?/).filter(p => p.trim()).length
    }
  },
  created() {
    this.getList()
  },
  beforeDestroy() {
    Object.values(this.pollingTimers).forEach(clearInterval)
  },
  methods: {
    getList() {
      this.loading = true
      const params = {
        skip: (this.queryParams.page - 1) * this.queryParams.limit,
        limit: this.queryParams.limit,
        name: this.queryParams.name || undefined
      }
      listExperiments(params).then(response => {
        const items = (response && response.items) ? response.items : []
        this.experimentList = items
        this.total = (response && response.total != null) ? response.total : items.length
        this.loading = false
        this.experimentList.forEach(exp => {
          if (exp.status === 'running') {
            this.startPolling(exp.id)
          }
        })
      }).catch(error => {
        console.error('获取实验列表失败:', error)
        this.$modal.msgError('获取实验列表失败')
        this.loading = false
      })
    },
    handleQuery() {
      this.queryParams.page = 1
      this.getList()
    },
    resetQuery() {
      this.resetForm('queryForm')
      this.handleQuery()
    },
    handleCreate() {
      this.$router.push('/geo/experiments/create')
    },
    handleView(row) {
      this.$router.push(`/geo/experiments/detail/${row.id}`)
    },
    handleRun(row) {
      this.runForm.experimentId = row.id
      this.runForm.questionsText = ''
      this.runForm.generator_mode = 'random'
      this.runForm.num_rounds = 1
      this.runForm.manualPrompt = ''
      this.runForm.sourcePrompt = ''
      this.runForm.enable_llm_scorer = true
      this.runDialogVisible = true
    },
    handleTrain(row) {
      this.trainForm.experimentId = row.id
      this.trainForm.algorithm = 'ppo'
      this.trainForm.total_timesteps = 1000
      this.trainForm.questionsText = ''
      this.trainForm.hyper = { log_every: '', n_steps: '', batch_size: '', lr: '', gamma: '', buffer_size: '', learning_starts: '' }
      this.trainForm.enable_llm_scorer = true
      this.trainDialogVisible = true
    },
    submitTrain() {
      if (!this.trainForm.questionsText.trim()) { this.$modal.msgError('请输入问题列表'); return }
      const questions = this.trainForm.questionsText.split('\n').filter(q => q.trim())
      if (questions.length === 0) { this.$modal.msgError('请至少输入一个问题'); return }
      const h = this.trainForm.hyper
      const hyperParams = {}
      if (h.log_every.trim()) hyperParams.log_every = parseInt(h.log_every, 10)
      if (h.lr.trim()) hyperParams.learning_rate = parseFloat(h.lr)
      if (h.gamma.trim()) hyperParams.gamma = parseFloat(h.gamma)
      if (h.batch_size.trim()) hyperParams.batch_size = parseInt(h.batch_size, 10)
      if (this.trainForm.algorithm === 'ppo') {
        if (h.n_steps.trim()) hyperParams.n_steps = parseInt(h.n_steps, 10)
      } else {
        if (h.buffer_size.trim()) hyperParams.buffer_size = parseInt(h.buffer_size, 10)
        if (h.learning_starts.trim()) hyperParams.learning_starts = parseInt(h.learning_starts, 10)
      }
      const data = {
        experiment_id: this.trainForm.experimentId,
        algorithm: this.trainForm.algorithm,
        total_timesteps: this.trainForm.total_timesteps,
        questions: questions,
        hyper_params: hyperParams,
        enable_llm_scorer: this.trainForm.enable_llm_scorer
      }
      this.trainSubmitting = true
      startTraining(data).then(response => {
        const run = response
        this.$modal.msgSuccess(`RL 训练已启动 (Training: ${run.id})，算法: ${run.algorithm.toUpperCase()}，状态: ${run.status}`)
        this.trainDialogVisible = false
      }).catch(() => {
        // 错误已由 request 拦截器统一处理
      }).finally(() => {
        this.trainSubmitting = false
      })
    },
    submitRun() {
      if (!this.runForm.questionsText.trim()) { this.$modal.msgError('请输入问题列表'); return }
      const questions = this.runForm.questionsText.split('\n').filter(q => q.trim())
      if (questions.length === 0) { this.$modal.msgError('请至少输入一个问题'); return }
      if (this.runForm.generator_mode === 'manual' && !this.runForm.manualPrompt.trim()) {
        this.$modal.msgError('请编写 System Prompt'); return
      }
      const experimentId = this.runForm.experimentId
      const data = {
        questions: questions,
        generator_mode: this.runForm.generator_mode,
        num_rounds: this.runForm.num_rounds,
        enable_llm_scorer: this.runForm.enable_llm_scorer
      }
      if (this.runForm.generator_mode === 'template_mutation') {
        data.source_prompt = this.runForm.sourcePrompt || undefined
      }
      if (this.runForm.generator_mode === 'manual') {
        data.manual_prompt = this.runForm.manualPrompt
      }
      runExperimentRound(experimentId, data).then((res) => {
        if (res.accepted) {
          this.$modal.msgSuccess(res.message || '任务已提交，后台执行中')
          this.runDialogVisible = false
          this.startPolling(experimentId)
          this.getList()
        } else {
          this.$modal.msgError('任务提交失败')
        }
      }).catch(() => {
        // 错误已由 request 拦截器统一处理
      })
    },
    startPolling(experimentId) {
      if (this.pollingTimers[experimentId]) return
      const timer = setInterval(() => {
        getExperiment(experimentId).then((exp) => {
          // Update the list row in-place
          const idx = this.experimentList.findIndex(e => e.id === experimentId)
          if (idx >= 0) {
            this.$set(this.experimentList, idx, { ...this.experimentList[idx], ...exp })
          }
          if (exp.status !== 'running' && exp.status !== 'paused') {
            this.stopPolling(experimentId)
            if (exp.status === 'finished') {
              this.$modal.msgSuccess(`实验 "${exp.name}" 运行完成（共 ${exp.current_round}/${exp.max_rounds} 轮，最佳奖励 ${Number(exp.best_reward).toFixed(4)}）`)
            } else if (exp.status === 'failed') {
              this.$modal.msgError(`实验 "${exp.name}" 运行失败，请检查后台日志`)
            }
          }
        }).catch(() => {
          this.stopPolling(experimentId)
        })
      }, 2000)
      this.pollingTimers[experimentId] = timer
    },
    stopPolling(experimentId) {
      const timer = this.pollingTimers[experimentId]
      if (timer) {
        clearInterval(timer)
        this.$delete(this.pollingTimers, experimentId)
      }
    },
    handlePause(row) {
      this.$modal.confirm(`确认暂停实验 "${row.name}" ？`).then(() => {
        pauseExperiment(row.id).then(() => {
          this.$modal.msgSuccess('实验已暂停')
          this.getList()
        }).catch(() => {})
      }).catch(() => {})
    },
    handleResume(row) {
      this.$modal.confirm(`确认恢复实验 "${row.name}" ？`).then(() => {
        resumeExperiment(row.id).then(() => {
          this.$modal.msgSuccess('实验已恢复运行')
          this.startPolling(row.id)
          this.getList()
        }).catch(() => {})
      }).catch(() => {})
    },
    handleDelete(row) {
      this.$modal.confirm(`确认删除实验 "${row.name}" ？`).then(() => {
        deleteExperiment(row.id).then(() => {
          this.$modal.msgSuccess('删除成功')
          this.getList()
        }).catch(() => {
        })
      }).catch(() => {})
    },
    getStatusType(status) {
      return { running: 'success', finished: 'info', failed: 'danger', created: 'warning', paused: 'warning' }[status] || ''
    },
    statusLabel(status) {
      return { created: '未运行', running: '运行中', finished: '已完成', failed: '失败', paused: '已暂停' }[status] || status
    },
    parseTime(time) {
      if (!time) return '-'
      return new Date(time).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.box-card { margin-bottom: 20px; }
.form-tip { font-size: 12px; color: #909399; margin-top: 5px; line-height: 1.5; }
</style>
