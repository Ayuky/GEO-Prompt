import request from '@/utils/request'

// 查询提示词信息列表
export function listVersions(query) {
  return request({
    url: '/geo/versions/list',
    method: 'get',
    params: query
  })
}

// 查询提示词信息详细
export function getVersions(id) {
  return request({
    url: '/geo/versions/' + id,
    method: 'get'
  })
}

// 新增提示词信息
export function addVersions(data) {
  return request({
    url: '/geo/versions',
    method: 'post',
    data: data
  })
}

// 修改提示词信息
export function updateVersions(data) {
  return request({
    url: '/geo/versions',
    method: 'put',
    data: data
  })
}

// 删除提示词信息
export function delVersions(id) {
  return request({
    url: '/geo/versions/' + id,
    method: 'delete'
  })
}

// 查询提示词信息统计信息
export function getVersionsStats(query) {
  return request({
    url: '/geo/versions/stats',
    method: 'get',
    params: query
  })
}
