import request from '@/utils/request'

export function listModels(params) {
  return request({
    url: '/geo/models',
    method: 'get',
    params: params
  })
}

export function getModel(id) {
  return request({
    url: '/geo/models/' + id,
    method: 'get'
  })
}

export function createModel(data) {
  return request({
    url: '/geo/models',
    method: 'post',
    data: data
  })
}

export function updateModel(id, data) {
  return request({
    url: '/geo/models/' + id,
    method: 'put',
    data: data
  })
}

export function deleteModel(id) {
  return request({
    url: '/geo/models/' + id,
    method: 'delete'
  })
}
