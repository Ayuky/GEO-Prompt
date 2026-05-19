import request from '@/utils/request'

// 启动 RL 训练
export function startTraining(data) {
  return request({
    url: '/geo/trainings/start',
    method: 'post',
    data: data,
    timeout: 120000
  })
}

// 获取训练任务列表
export function listTrainingRuns(params) {
  return request({
    url: '/geo/trainings/',
    method: 'get',
    params: params
  })
}

// 获取训练任务详情
export function getTrainingRun(runId) {
  return request({
    url: '/geo/trainings/' + runId,
    method: 'get'
  })
}

// 暂停训练
export function pauseTraining(runId) {
  return request({
    url: '/geo/trainings/' + runId + '/pause',
    method: 'post'
  })
}

// 恢复训练
export function resumeTraining(runId) {
  return request({
    url: '/geo/trainings/' + runId + '/resume',
    method: 'post'
  })
}

// 获取训练指标（按 timestep 升序）
export function getTrainingMetrics(runId) {
  return request({
    url: '/geo/trainings/' + runId + '/metrics',
    method: 'get'
  })
}
