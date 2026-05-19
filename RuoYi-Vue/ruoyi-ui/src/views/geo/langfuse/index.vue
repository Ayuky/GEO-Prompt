<template>
  <div class="app-container">
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>Langfuse 追踪列表</span>
      </div>

      <el-form :model="queryParams" ref="queryForm" size="small" :inline="true" label-width="80px">
        <el-form-item label="追踪名称" prop="name">
          <el-input v-model="queryParams.name" placeholder="按名称过滤" clearable @keyup.enter.native="handleQuery" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
          <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="traceList" border @row-click="handleRowClick" style="cursor: pointer">
        <el-table-column label="追踪ID" align="center" prop="id" min-width="280" show-overflow-tooltip />
        <el-table-column label="名称" align="center" prop="name" min-width="160" show-overflow-tooltip />
        <el-table-column label="耗时(ms)" align="center" prop="latency" width="100">
          <template slot-scope="scope">
            {{ scope.row.latency != null ? scope.row.latency : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="时间" align="center" prop="timestamp" width="180">
          <template slot-scope="scope">{{ formatTime(scope.row.timestamp) }}</template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="100" fixed="right">
          <template slot-scope="scope">
            <el-button size="mini" type="text" icon="el-icon-view" @click.stop="handleView(scope.row)">查看</el-button>
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
  </div>
</template>

<script>
import { listTraces } from '@/api/geo/langfuse'

export default {
  name: 'LangfuseEmbed',
  data() {
    return {
      loading: true,
      traceList: [],
      total: 0,
      queryParams: { page: 1, limit: 10, name: '' }
    }
  },
  created() {
    this.getList()
  },
  methods: {
    getList() {
      this.loading = true
      const params = {
        page: this.queryParams.page,
        limit: this.queryParams.limit,
        name: this.queryParams.name || undefined
      }
      listTraces(params).then(response => {
        const data = response.data || response
        this.traceList = data || []
        this.total = response.meta ? response.meta.totalItems : (data ? data.length : 0)
        this.loading = false
      }).catch(() => {
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
    handleRowClick(row) {
      this.$router.push(`/geo/langfuse/trace/${row.id}`)
    },
    handleView(row) {
      this.$router.push(`/geo/langfuse/trace/${row.id}`)
    },
    formatTime(timestamp) {
      if (!timestamp) return '-'
      return new Date(timestamp).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.box-card { margin-bottom: 20px; }
</style>
