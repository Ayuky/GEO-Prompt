import { saveAs } from 'file-saver'

const BOM = '﻿'
const MAX_PAGE_SIZE = 100

function escapeCSV(value) {
  if (value === null || value === undefined) return ''
  const str = String(value)
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return '"' + str.replace(/"/g, '""') + '"'
  }
  return str
}

export function exportToCSV(headers, rows, filename) {
  const lines = [BOM + headers.map(escapeCSV).join(',')]
  for (const row of rows) {
    lines.push(headers.map(h => escapeCSV(row[h])).join(','))
  }
  const blob = new Blob([lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  saveAs(blob, filename)
}

/**
 * 分页拉取全部数据。
 * @param {Function} fetchFn — 接收 { pageNum, pageSize }，返回 Promise<{ items: Array, total: number }>
 * @returns {Promise<Array>} 全部 items
 */
export async function fetchAllPages(fetchFn) {
  const first = await fetchFn({ pageNum: 1, pageSize: MAX_PAGE_SIZE })
  const items = Array.isArray(first) ? first : (first.items || [])
  const total = first.total != null ? first.total : items.length

  if (total <= MAX_PAGE_SIZE) return items

  const totalPages = Math.ceil(total / MAX_PAGE_SIZE)
  const requests = []
  for (let p = 2; p <= totalPages; p++) {
    requests.push(fetchFn({ pageNum: p, pageSize: MAX_PAGE_SIZE }))
  }
  const results = await Promise.all(requests)
  for (const res of results) {
    const batch = Array.isArray(res) ? res : (res.items || [])
    items.push(...batch)
  }
  return items
}
