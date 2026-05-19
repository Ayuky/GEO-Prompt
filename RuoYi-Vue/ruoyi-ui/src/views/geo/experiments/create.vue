<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>创建新实验</span>
        <el-button
          style="float: right; padding: 10px 10px;font-weight: bold; box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4); transition: all 0.3s;"
          type="primary"
          size="medium"@click="goBack"
        >返回列表</el-button>
      </div>

      <el-form
        ref="form"
        :model="form"
        :rules="rules"
        label-width="140px"
        class="experiment-form"
      >
        <!-- 基本信息 -->
        <el-divider content-position="left">基本信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="实验名称" prop="name">
              <el-input id="name" v-model="form.name" placeholder="请输入实验名称" maxlength="128" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大轮次" prop="max_rounds">
              <el-input-number v-model="form.max_rounds" :min="1" :max="1000" controls-position="right" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="业务领域" prop="domain">
              <el-select v-model="form.domain" placeholder="请选择业务领域" style="width: 100%">
                <el-option label="汽车品牌" value="automotive_brand_geo" />
                <el-option label="数码科技" value="digital_tech" />
                <el-option label="家居生活" value="home_lifestyle" />
                <el-option label="美妆护肤" value="beauty_skincare" />
                <el-option label="运动健身" value="sports_fitness" />
                <el-option label="教育培训" value="education_training" />
                <el-option label="金融理财" value="finance_investment" />
                <el-option label="旅游出行" value="travel_tourism" />
                <el-option label="美食餐饮" value="food_dining" />
                <el-option label="医疗健康" value="healthcare" />
                <el-option label="通用领域" value="general" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="实验描述" prop="description">
          <el-input type="textarea" v-model="form.description" :rows="3" placeholder="请输入实验描述（可选）" />
        </el-form-item>

        <!-- 模型配置 -->
        <el-divider content-position="left">模型配置</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item prop="model_id">
              <template slot="label">生成模型</template>
              <el-select
                id="model_id"
                v-model="form.model_id"
                placeholder="请选择 LLM 模型"
                filterable
                style="width: 100%"
                @change="handleModelChange"
              >
                <el-option
                  v-for="m in activeModels"
                  :key="m.id"
                  :label="`${m.name} (${m.model_name})`"
                  :value="m.id"
                >
                  <span style="float:left">{{ m.name }}</span>
                  <span style="float:right;color:#8492a6;font-size:13px">{{ m.model_name }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 评分器配置 -->
        <el-divider content-position="left">LLM 评分器配置</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item prop="judge_model_id">
              <template slot="label">评分模型</template>
              <el-select
                id="judge_model_id"
                v-model="form.judge_model_id"
                placeholder="请选择评分模型"
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="m in activeModels"
                  :key="m.id"
                  :label="`${m.name} (${m.model_name})`"
                  :value="m.id"
                >
                  <span style="float:left">{{ m.name }}</span>
                  <span style="float:right;color:#8492a6;font-size:13px">{{ m.model_name }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 目标实体 -->
        <el-divider content-position="left">目标实体配置</el-divider>

        <el-form-item prop="target_entities">
          <template slot="label">目标实体列表</template>
          <el-select
            id="target_entities"
            v-model="form.target_entities"
            multiple filterable allow-create default-first-option
            placeholder="请输入或选择目标实体（如：比亚迪、特斯拉等）"
            style="width: 100%"
          >
            <el-option v-for="item in commonEntities" :key="item" :label="item" :value="item" />
          </el-select>
          <div class="form-tip">可以手动输入新的实体，也可以从常用实体中选择</div>
        </el-form-item>

        <!-- 上下文配置 -->
        <el-divider content-position="left">上下文配置</el-divider>

        <el-form-item label="上下文文本" prop="context_text">
          <el-input
            type="textarea" v-model="form.context_text" :rows="4"
            placeholder="请输入用户上下文信息，例如：用户偏好家用SUV，预算20-30万"
          />
          <div class="form-tip">上下文将用于评估 Prompt 生成的质量和相关性</div>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button type="primary" @click="submitForm" :loading="submitLoading">创建实验</el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 快速配置模板 -->
    <el-card class="box-card template-card">
      <div slot="header"><span>快速配置模板</span></div>
      <el-row :gutter="10">
        <el-col :span="8">
          <el-button type="info" plain style="width:100%;margin-bottom:10px" @click="applyTemplate('automotive')">
            汽车评测场景
          </el-button>
        </el-col>
        <el-col :span="8">
          <el-button type="success" plain style="width:100%;margin-bottom:10px" @click="applyTemplate('ecommerce')">
            电商产品推荐
          </el-button>
        </el-col>
        <el-col :span="8">
          <el-button type="warning" plain style="width:100%;margin-bottom:10px" @click="applyTemplate('travel')">
            旅游出行规划
          </el-button>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import { createExperiment } from '@/api/geo/experiments'
import { listModels } from '@/api/geo/models'

export default {
  name: 'CreateExperiment',
  data() {
    return {
      submitLoading: false,
      loadingModels: false,
      activeModels: [],
      form: {
        name: '',
        domain: '',
        description: '',
        model_id: null,
        judge_model_id: null,
        target_entities: [],
        context_text: '',
        max_rounds: 100
      },
      rules: {
        name: [
          { required: true, message: '请输入实验名称', trigger: 'blur' },
          { min: 2, max: 128, message: '长度在 2 到 128 个字符', trigger: 'blur' }
        ],
        domain: [
          { required: true, message: '请选择业务领域', trigger: 'change' }
        ],
        model_id: [
          { required: true, message: '请选择生成模型', trigger: 'change' }
        ],
        judge_model_id: [
          { required: true, message: '请选择评分模型', trigger: 'change' }
        ],
        max_rounds: [
          { required: true, message: '请输入最大轮次', trigger: 'blur' }
        ],
        target_entities: [
          { type: 'array', required: true, message: '请至少添加一个目标实体', trigger: 'change' }
        ]
      },
      commonEntities: [
        '比亚迪', '特斯拉', '理想', '问界', '蔚来', '小鹏',
        '小米汽车', '极氪', '领克', '吉利', '长安', '长城'
      ]
    }
  },
  created() {
    this.loadModels()
  },
  methods: {
    loadModels() {
      this.loadingModels = true
      listModels({ active_only: true }).then(res => {
        this.activeModels = Array.isArray(res) ? res : []
      }).catch(() => {
        this.$modal.msgError('加载模型列表失败')
      }).finally(() => {
        this.loadingModels = false
      })
    },
    handleModelChange() {
      // no-op, keep for future model-dependent logic
    },
    applyTemplate(template) {
      const templates = {
        automotive: {
          name: 'auto-brand-geo-v1',
          domain: '汽车品牌',
          target_entities: ['比亚迪', '特斯拉', '理想', '问界'],
          context_text: '用户偏好家用SUV，预算20-30万',
          max_rounds: 100,
          description: '汽车品牌 GEO Prompt 优化实验'
        },
        ecommerce: {
          name: 'product-recommend-v1',
          domain: '电商产品',
          target_entities: ['iPhone 15 Pro', '华为Mate60', '小米14', '三星Galaxy S24'],
          context_text: '用户需要一款拍照效果好、续航能力强、性价比高的手机，预算5000-7000元',
          max_rounds: 100,
          description: '电商产品推荐 GEO Prompt 优化实验'
        },
        travel: {
          name: 'travel-planning-v1',
          domain: '旅游出行',
          target_entities: ['云南大理', '四川成都', '海南三亚', '浙江杭州'],
          context_text: '用户计划春节假期出游，偏好温暖气候和文化体验，预算人均5000-8000元，出行时间5-7天',
          max_rounds: 100,
          description: '旅游目的地规划 GEO Prompt 优化实验'
        }
      }
      const selected = templates[template]
      if (selected) {
        Object.assign(this.form, selected)
        this.$modal.msgSuccess('已应用模板配置')
      }
    },
    submitForm() {
      this.$refs['form'].validate(valid => {
        if (!valid) return
        if (this.form.target_entities.length === 0) {
          this.$modal.msgWarning('建议至少添加一个目标实体')
          return
        }
        this.submitLoading = true
        const submitData = {
          name: this.form.name,
          domain: this.form.domain,
          description: this.form.description || '',
          model_id: this.form.model_id,
          judge_model_id: this.form.judge_model_id,
          target_entities: this.form.target_entities.filter(e => e.trim()),
          context_text: this.form.context_text || '',
          max_rounds: this.form.max_rounds
        }
        createExperiment(submitData).then(() => {
          this.$modal.msgSuccess('实验创建成功')
          this.$router.replace('/geo/experiments')
        }).catch(error => {
          const errMsg = error?.response?.data?.detail || error?.response?.data?.msg || error?.message || (typeof error === 'string' ? error : '未知错误')
          this.$modal.msgError('创建失败: ' + errMsg)
        }).finally(() => {
          this.submitLoading = false
        })
      })
    },
    resetForm() {
      this.$refs['form'].resetFields()
      this.activeModels = []
      this.form.domain = ''
    },
    goBack() {
      this.$router.back()
    }
  }
}
</script>

<style scoped>
.experiment-form {
  max-width: 1200px;
  margin: 0 auto;
}
.template-card {
  margin-top: 20px;
}
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
  line-height: 1.5;
}
.el-divider__text {
  font-weight: bold;
  color: #303133;
}
</style>
