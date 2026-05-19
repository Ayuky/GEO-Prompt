import request from '@/utils/request'

// 查询评估记录列表
export function listRecords(query) {
  return request({
    url: '/geo/records/list',
    method: 'get',
    params: query
  })
}

// 查询评估记录详细
export function getRecords(id) {
  return request({
    url: '/geo/records/' + id,
    method: 'get'
  })
}

// 新增评估记录
export function addRecords(data) {
  return request({
    url: '/geo/records',
    method: 'post',
    data: data
  })
}

// 修改评估记录
export function updateRecords(data) {
  return request({
    url: '/geo/records',
    method: 'put',
    data: data
  })
}

// 删除评估记录
export function delRecords(id) {
  return request({
    url: '/geo/records/' + id,
    method: 'delete'
  })
}

// 查询评估记录统计信息
export function getRecordsStats(query) {
  return request({
    url: '/geo/records/stats',
    method: 'get',
    params: query
  })
}

// 查询评估记录汇总信息
export function getRecordsSummary() {
  return request({
    url: '/geo/records/summary',
    method: 'get'
  })
}
