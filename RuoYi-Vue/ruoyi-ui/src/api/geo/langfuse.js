import request from '@/utils/request'

const BASE = '/geo/langfuse'

// ========== Traces ==========

export function listTraces(params) {
  return request({
    url: `${BASE}/api/public/traces`,
    method: 'get',
    params
  })
}

export function getTrace(traceId) {
  return request({
    url: `${BASE}/api/public/traces/${traceId}`,
    method: 'get'
  })
}

export function deleteTrace(traceId) {
  return request({
    url: `${BASE}/api/public/traces/${traceId}`,
    method: 'delete'
  })
}

// ========== Observations ==========

export function listObservations(params) {
  return request({
    url: `${BASE}/api/public/observations`,
    method: 'get',
    params
  })
}

export function getObservation(observationId) {
  return request({
    url: `${BASE}/api/public/observations/${observationId}`,
    method: 'get'
  })
}

export function listObservationsV2(params) {
  return request({
    url: `${BASE}/api/public/v2/observations`,
    method: 'get',
    params
  })
}

// ========== Scores ==========

export function listScores(params) {
  return request({
    url: `${BASE}/api/public/scores`,
    method: 'get',
    params
  })
}

// ========== Sessions ==========

export function listSessions(params) {
  return request({
    url: `${BASE}/api/public/sessions`,
    method: 'get',
    params
  })
}

export function getSession(sessionId) {
  return request({
    url: `${BASE}/api/public/sessions/${sessionId}`,
    method: 'get'
  })
}

// ========== Health ==========

export function checkHealth() {
  return request({
    url: `${BASE}/api/public/health`,
    method: 'get'
  })
}
