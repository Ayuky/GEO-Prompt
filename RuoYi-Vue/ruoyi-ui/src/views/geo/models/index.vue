<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>LLM模型管理</span>
        <el-button
          style="float: right; padding: 3px 0"
          type="primary"
          icon="el-icon-plus"
          @click="handleAdd"
        >添加模型</el-button>
      </div>

      <el-table v-loading="loading" :data="modelList" border>
        <el-table-column label="ID" align="center" prop="id" width="80" />
        <el-table-column label="模型名称" align="center" prop="name" min-width="140">
          <template slot-scope="scope">
            <span>{{ scope.row.name }}</span>
            <el-tag v-if="!scope.row.is_active" type="danger" size="mini" style="margin-left:8px">已停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="API 地址" align="center" prop="base_url" min-width="240" :show-overflow-tooltip="true" />
        <el-table-column label="模型标识" align="center" prop="model_name" min-width="160">
          <template slot-scope="scope">
            <el-tag type="info" size="small">{{ scope.row.model_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="API Key" align="center" width="180">
          <template slot-scope="scope">
            <span style="font-family: monospace; color: #909399">{{ scope.row.api_key_masked }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" align="center" width="90">
          <template slot-scope="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
              {{ scope.row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" align="center" width="170">
          <template slot-scope="scope">
            {{ formatTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="160" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" type="text" icon="el-icon-edit" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="mini" type="text" icon="el-icon-delete" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && modelList.length === 0" description="暂无模型配置，请添加" />
    </el-card>

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="560px" :close-on-click-modal="false">
      <el-form ref="modelForm" :model="form" :rules="rules" label-width="110px">
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" placeholder="自定义标识，如：公司DeepSeek" maxlength="64" show-word-limit />
          <div class="form-tip">用于在系统中识别该模型配置，不可重复</div>
        </el-form-item>
        <el-form-item label="API 地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="如：https://api.deepseek.com/" maxlength="512" />
          <div class="form-tip">需兼容 OpenAI API 格式，末尾可带 /v1</div>
        </el-form-item>
        <el-form-item label="模型标识" prop="model_name">
          <el-input v-model="form.model_name" placeholder="如：deepseek-v4-flash" maxlength="128" />
          <div class="form-tip">调用 API 时传入的 model 参数值</div>
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="请输入 API Key" />
        </el-form-item>
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { listModels, getModel, createModel, updateModel, deleteModel } from '@/api/geo/models'

export default {
  name: 'GeopromptModels',
  data() {
    return {
      loading: false,
      modelList: [],
      dialogVisible: false,
      dialogTitle: '',
      submitLoading: false,
      isEdit: false,
      editingId: null,
      form: {
        name: '',
        base_url: '',
        model_name: '',
        api_key: '',
        is_active: true
      },
      rules: {
        name: [
          { required: true, message: '请输入模型名称', trigger: 'blur' },
          { min: 1, max: 64, message: '长度 1-64', trigger: 'blur' }
        ],
        base_url: [
          { required: true, message: '请输入 API 地址', trigger: 'blur' }
        ],
        model_name: [
          { required: true, message: '请输入模型标识', trigger: 'blur' }
        ],
        api_key: [
          { required: true, message: '请输入 API Key', trigger: 'blur' }
        ]
      }
    }
  },
  created() {
    this.getList()
  },
  methods: {
    getList() {
      this.loading = true
      listModels().then(res => {
        this.modelList = Array.isArray(res) ? res : []
        this.loading = false
      }).catch(() => {
        this.$modal.msgError('加载模型列表失败')
        this.loading = false
      })
    },
    handleAdd() {
      this.isEdit = false
      this.editingId = null
      this.dialogTitle = '添加模型'
      this.resetForm()
      this.dialogVisible = true
    },
    handleEdit(row) {
      this.isEdit = true
      this.editingId = row.id
      this.dialogTitle = '编辑模型'
      this.form.name = row.name
      this.form.base_url = row.base_url
      this.form.model_name = row.model_name
      this.form.api_key = ''
      this.form.is_active = row.is_active
      this.dialogVisible = true
    },
    handleDelete(row) {
      this.$modal.confirm(`确认删除模型 "${row.name}" ？删除后关联的实验将无法正常运行。`).then(() => {
        deleteModel(row.id).then(() => {
          this.$modal.msgSuccess('删除成功')
          this.getList()
        }).catch(() => {
          // 错误已由 request 拦截器统一处理
        })
      }).catch(() => {})
    },
    submitForm() {
      this.$refs.modelForm.validate(valid => {
        if (!valid) return
        this.submitLoading = true
        const data = {
          name: this.form.name,
          base_url: this.form.base_url,
          model_name: this.form.model_name,
          api_key: this.form.api_key
        }
        if (this.isEdit) {
          data.is_active = this.form.is_active
          if (!data.api_key) delete data.api_key
        }
        const request = this.isEdit
          ? updateModel(this.editingId, data)
          : createModel(data)
        request.then(() => {
          this.$modal.msgSuccess(this.isEdit ? '更新成功' : '创建成功')
          this.dialogVisible = false
          this.getList()
        }).catch(() => {
          // 错误已由 request 拦截器统一处理
        }).finally(() => {
          this.submitLoading = false
        })
      })
    },
    resetForm() {
      this.form = { name: '', base_url: '', model_name: '', api_key: '', is_active: true }
      this.$nextTick(() => {
        if (this.$refs.modelForm) this.$refs.modelForm.clearValidate()
      })
    },
    formatTime(time) {
      if (!time) return '-'
      return new Date(time).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
