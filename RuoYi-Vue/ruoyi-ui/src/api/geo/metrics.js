import request from '@/utils/request'

// 查询训练指标列表
export function listMetrics(query) {
  return request({
    url: '/geo/metrics/list',
    method: 'get',
    params: query
  })
}

// 查询训练指标详细
export function getMetrics(id) {
  return request({
    url: '/geo/metrics/' + id,
    method: 'get'
  })
}

// 新增训练指标
export function addMetrics(data) {
  return request({
    url: '/geo/metrics',
    method: 'post',
    data: data
  })
}

// 修改训练指标
export function updateMetrics(data) {
  return request({
    url: '/geo/metrics',
    method: 'put',
    data: data
  })
}

// 删除训练指标
export function delMetrics(id) {
  return request({
    url: '/geo/metrics/' + id,
    method: 'delete'
  })
}

// 查询训练指标统计信息
export function getMetricsStats(query) {
  return request({
    url: '/geo/metrics/stats',
    method: 'get',
    params: query
  })
}
