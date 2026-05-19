import request from '@/utils/request'

// 创建实验
export function createExperiment(data) {
  return request({
    url: '/geo/experiments',
    method: 'post',
    data: data
  })
}

// 获取实验详情
export function getExperiment(experimentId) {
  return request({
    url: '/geo/experiments/' + experimentId,
    method: 'get'
  })
}

// 运行实验轮次（异步，立即返回）
export function runExperimentRound(experimentId, data) {
  return request({
    url: '/geo/experiments/' + experimentId + '/run',
    method: 'post',
    data: data,
    timeout: 30000
  })
}

// 获取实验版本历史（收敛曲线数据）
export function getExperimentVersions(experimentId) {
  return request({
    url: '/geo/experiments/' + experimentId + '/versions',
    method: 'get'
  })
}

// 获取实验列表
export function listExperiments(params) {
  return request({
    url: '/geo/experiments',
    method: 'get',
    params: {
      skip: params.skip != null ? params.skip : 0,
      limit: params.limit || 20,
      name: params.name || undefined,
      model_id: params.model_id || undefined,
      status: params.status || undefined
    }
  })
}

// 删除实验
export function deleteExperiment(id) {
  return request({
    url: '/geo/experiments/' + id,
    method: 'delete'
  })
}

// 暂停实验
export function pauseExperiment(experimentId) {
  return request({
    url: '/geo/experiments/' + experimentId + '/pause',
    method: 'post'
  })
}

// 恢复实验
export function resumeExperiment(experimentId) {
  return request({
    url: '/geo/experiments/' + experimentId + '/resume',
    method: 'post'
  })
}