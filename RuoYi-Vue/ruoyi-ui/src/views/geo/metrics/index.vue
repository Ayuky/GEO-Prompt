<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryForm" size="small" :inline="true" v-show="showSearch" label-width="80px">
      <el-form-item label="训练ID" prop="trainingRunId">
        <el-input
          v-model="queryParams.trainingRunId"
          placeholder="请输入训练运行ID"
          clearable
          @keyup.enter.native="handleQuery"
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item label="时间步长" prop="timestep">
        <el-input
          v-model="queryParams.timestep"
          placeholder="请输入时间步长"
          clearable
          @keyup.enter.native="handleQuery"
          style="width: 140px"
        />
      </el-form-item>
      <el-form-item label="奖励范围">
        <el-input
          v-model="queryParams.rewardMin"
          placeholder="最小"
          clearable
          style="width: 90px"
        />
        <span style="margin: 0 6px; color: #c0c4cc;">-</span>
        <el-input
          v-model="queryParams.rewardMax"
          placeholder="最大"
          clearable
          style="width: 90px"
        />
      </el-form-item>
      <el-form-item label="创建时间" prop="createdAt">
        <el-date-picker clearable
          v-model="queryParams.createdAt"
          type="date"
          value-format="yyyy-MM-dd"
          placeholder="请选择创建时间"
          style="width: 150px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="el-icon-plus"
          size="mini"
          @click="handleAdd"
          v-hasPermi="['geo:metrics:add']"
        >新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="el-icon-edit"
          size="mini"
          :disabled="single"
          @click="handleUpdate"
          v-hasPermi="['geo:metrics:edit']"
        >修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="el-icon-delete"
          size="mini"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['geo:metrics:remove']"
        >删除</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="warning"
          plain
          icon="el-icon-download"
          size="mini"
          @click="handleExport"
          v-hasPermi="['geo:metrics:export']"
        >导出</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList" />
    </el-row>

    <el-table v-loading="loading" :data="metricsList" @selection-change="handleSelectionChange" border>
      <el-table-column type="selection" width="45" align="center" />
      <el-table-column label="ID" align="center" prop="id" width="70" />
      <el-table-column label="训练运行ID" align="center" prop="trainingRunId" width="110" />
      <el-table-column label="时间步长" align="center" prop="timestep" width="90" />
      <el-table-column label="奖励" align="center" width="90">
        <template slot-scope="scope">
          <el-tag :type="rewardTagType(scope.row.reward)" size="small">
            {{ formatScore(scope.row.reward) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="熵损失" align="center" prop="entropyLoss" width="90">
        <template slot-scope="scope">
          {{ formatScore(scope.row.entropyLoss) }}
        </template>
      </el-table-column>
      <el-table-column label="价值损失" align="center" prop="valueLoss" width="90">
        <template slot-scope="scope">
          {{ formatScore(scope.row.valueLoss) }}
        </template>
      </el-table-column>
      <el-table-column label="策略损失" align="center" prop="policyLoss" width="90">
        <template slot-scope="scope">
          {{ formatScore(scope.row.policyLoss) }}
        </template>
      </el-table-column>
      <el-table-column label="指标JSON" align="center" prop="metricsJson" min-width="120" :show-overflow-tooltip="true" />
      <el-table-column label="创建时间" align="center" width="110">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.createdAt, '{y}-{m}-{d}') }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="130" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button
            size="mini"
            type="text"
            icon="el-icon-edit"
            @click="handleUpdate(scope.row)"
            v-hasPermi="['geo:metrics:edit']"
          >修改</el-button>
          <el-button
            size="mini"
            type="text"
            icon="el-icon-delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['geo:metrics:remove']"
          >删除</el-button>
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

    <el-dialog :title="title" :visible.sync="open" width="550px" append-to-body>
      <el-form ref="form" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="训练运行ID" prop="trainingRunId">
          <el-input v-model="form.trainingRunId" placeholder="请输入训练运行ID" />
        </el-form-item>
        <el-form-item label="时间步长" prop="timestep">
          <el-input-number
            v-model="form.timestep"
            :min="0"
            :step="100"
            controls-position="right"
            style="width: 100%"
            placeholder="请输入时间步长"
          />
        </el-form-item>
        <el-form-item label="奖励" prop="reward">
          <el-input v-model="form.reward" placeholder="请输入奖励值" />
        </el-form-item>
        <el-form-item label="熵损失" prop="entropyLoss">
          <el-input v-model="form.entropyLoss" placeholder="请输入熵损失" />
        </el-form-item>
        <el-form-item label="价值损失" prop="valueLoss">
          <el-input v-model="form.valueLoss" placeholder="请输入价值损失" />
        </el-form-item>
        <el-form-item label="策略损失" prop="policyLoss">
          <el-input v-model="form.policyLoss" placeholder="请输入策略损失" />
        </el-form-item>
        <el-form-item label="指标JSON" prop="metricsJson">
          <el-input
            v-model="form.metricsJson"
            type="textarea"
            :rows="4"
            placeholder="请输入指标JSON数据"
          />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancel">取 消</el-button>
        <el-button type="primary" @click="submitForm">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { listMetrics, getMetrics, delMetrics, addMetrics, updateMetrics } from "@/api/geo/metrics"

export default {
  name: "Metrics",
  data() {
    return {
      loading: true,
      ids: [],
      single: true,
      multiple: true,
      showSearch: true,
      total: 0,
      metricsList: [],
      title: "",
      open: false,
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        trainingRunId: null,
        timestep: null,
        rewardMin: null,
        rewardMax: null,
        createdAt: null
      },
      form: {},
      rules: {
        trainingRunId: [
          { required: true, message: "训练运行ID不能为空", trigger: "blur" }
        ],
        timestep: [
          { required: true, message: "时间步长不能为空", trigger: "blur" }
        ],
        reward: [
          { required: true, message: "奖励不能为空", trigger: "blur" }
        ],
        entropyLoss: [
          { required: true, message: "熵损失不能为空", trigger: "blur" }
        ],
        valueLoss: [
          { required: true, message: "价值损失不能为空", trigger: "blur" }
        ],
        policyLoss: [
          { required: true, message: "策略损失不能为空", trigger: "blur" }
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
      listMetrics(this.queryParams).then(response => {
        const items = (response && response.items) ? response.items : []
        this.metricsList = items
        this.total = (response && response.total != null) ? response.total : items.length
        this.loading = false
      })
    },
    cancel() {
      this.open = false
      this.reset()
    },
    reset() {
      this.form = {
        id: null,
        trainingRunId: null,
        timestep: null,
        reward: null,
        entropyLoss: null,
        valueLoss: null,
        policyLoss: null,
        metricsJson: null
      }
      this.resetForm("form")
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
    handleAdd() {
      this.reset()
      this.open = true
      this.title = "添加训练指标"
    },
    handleUpdate(row) {
      this.reset()
      const id = row.id || this.ids
      getMetrics(id).then(response => {
        this.form = response
        this.open = true
        this.title = "修改训练指标"
      })
    },
    submitForm() {
      this.$refs["form"].validate(valid => {
        if (valid) {
          if (this.form.id != null) {
            updateMetrics(this.form).then(() => {
              this.$modal.msgSuccess("修改成功")
              this.open = false
              this.getList()
            })
          } else {
            addMetrics(this.form).then(() => {
              this.$modal.msgSuccess("新增成功")
              this.open = false
              this.getList()
            })
          }
        }
      })
    },
    handleDelete(row) {
      const ids = row.id || this.ids
      this.$modal.confirm('是否确认删除训练指标编号为"' + ids + '"的数据项？').then(() => {
        return delMetrics(ids)
      }).then(() => {
        this.getList()
        this.$modal.msgSuccess("删除成功")
      }).catch(() => {})
    },
    handleExport() {
      this.download('geo/metrics/export', { ...this.queryParams }, `metrics_${new Date().getTime()}.xlsx`)
    },
    formatScore(value) {
      if (value === null || value === undefined) return '-'
      return Number(value).toFixed(4)
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
