/**
 * 统计数据格式化工具
 * 用于将后端API返回的统计数据转换为图表组件所需的数据格式
 */

/**
 * 从 API 数据中提取数组
 * 兼容两种格式：直接返回的数组 [...], 或带 data/list 字段的对象 { data: [...] }
 */
function extractData(apiData) {
  if (Array.isArray(apiData)) return apiData
  if (apiData && Array.isArray(apiData.data)) return apiData.data
  if (apiData && Array.isArray(apiData.list)) return apiData.list
  return []
}

/**
 * 从 API 数据中提取标题
 */
function extractTitle(apiData, defaultTitle) {
  return (apiData && apiData.title) || defaultTitle
}

/**
 * 将API响应转换为饼图数据格式
 * @param {Object} apiData - API返回的统计数据
 * @param {Object} config - 配置项
 * @param {string} config.nameKey - 数据项名称字段，默认'name'
 * @param {string} config.valueKey - 数据项值字段，默认'value'
 * @param {string} config.title - 图表标题，默认使用apiData.title或'数据分布'
 * @returns {Object} 饼图数据格式
 */
export function toPieChartData(apiData, config = {}) {
  const {
    nameKey = 'name',
    valueKey = 'value',
    title = extractTitle(apiData, '数据分布')
  } = config

  const data = extractData(apiData)

  return {
    title,
    legend: data.map(item => item[nameKey]),
    seriesData: data.map(item => ({
      name: item[nameKey],
      value: item[valueKey]
    }))
  }
}

/**
 * 将API响应转换为柱状图数据格式
 * @param {Object} apiData - API返回的统计数据
 * @param {Object} config - 配置项
 * @param {string} config.xAxisKey - X轴数据字段，默认'category'
 * @param {string} config.valueKey - 值字段，默认'value'
 * @param {string} config.seriesName - 系列名称，默认'数据'
 * @param {string} config.title - 图表标题，默认使用apiData.title或'数据对比'
 * @returns {Object} 柱状图数据格式
 */
export function toBarChartData(apiData, config = {}) {
  const {
    xAxisKey = 'category',
    valueKey = 'value',
    seriesName = '数据',
    title = extractTitle(apiData, '数据对比')
  } = config

  const data = extractData(apiData)

  return {
    title,
    xAxisData: data.map(item => item[xAxisKey]),
    seriesData: [{
      name: seriesName,
      data: data.map(item => item[valueKey])
    }]
  }
}

/**
 * 将API响应转换为折线图数据格式
 * @param {Object} apiData - API返回的统计数据
 * @param {Object} config - 配置项
 * @param {string} config.xAxisKey - X轴数据字段，默认'category'
 * @param {string} config.valueKey - 值字段，默认'value'
 * @param {string} config.seriesName - 系列名称，默认'数据'
 * @param {string} config.title - 图表标题，默认使用apiData.title或'趋势分析'
 * @returns {Object} 折线图数据格式
 */
export function toLineChartData(apiData, config = {}) {
  const {
    xAxisKey = 'category',
    valueKey = 'value',
    seriesName = '数据',
    title = extractTitle(apiData, '趋势分析')
  } = config

  const data = extractData(apiData)

  return {
    title,
    xAxisData: data.map(item => item[xAxisKey]),
    seriesData: [{
      name: seriesName,
      data: data.map(item => item[valueKey])
    }]
  }
}

/**
 * 实验模块特定格式化函数
 */
export const experimentsFormatter = {
  /**
   * 格式化实验状态分布数据
   * @param {Array} data - 原始数据
   * @returns {Array} 格式化后的数据
   */
  formatStatusData(data) {
    const statusMap = {
      'running': '进行中',
      'completed': '已完成',
      'failed': '失败',
      'pending': '待开始'
    }

    return data.map(item => ({
      ...item,
      name: statusMap[item.name] || item.name
    }))
  },

  /**
   * 将实验状态数据转换为饼图格式
   * @param {Object} apiData - API数据
   * @returns {Object} 饼图数据
   */
  toStatusPieChart(apiData) {
    const formattedData = this.formatStatusData(extractData(apiData))
    return toPieChartData({
      ...apiData,
      data: formattedData
    }, {
      title: '实验状态分布'
    })
  },

  /**
   * 将实验领域数据转换为柱状图格式
   * @param {Object} apiData - API数据
   * @returns {Object} 柱状图数据
   */
  toDomainBarChart(apiData) {
    return toBarChartData(apiData, {
      xAxisKey: 'domain',
      valueKey: 'count',
      seriesName: '实验数量',
      title: '实验领域分布'
    })
  }
}

/**
 * 指标模块特定格式化函数
 */
export const metricsFormatter = {
  /**
   * 将指标数据转换为折线图格式（时间序列）
   * @param {Object} apiData - API数据
   * @returns {Object} 折线图数据
   */
  toTimelineChart(apiData) {
    return toLineChartData(apiData, {
      xAxisKey: 'timestep',
      valueKey: 'value',
      seriesName: '指标值',
      title: '指标变化趋势'
    })
  }
}

/**
 * 版本模块特定格式化函数
 */
export const versionsFormatter = {
  /**
   * 将版本轮次数据转换为折线图格式
   * @param {Object} apiData - API数据
   * @returns {Object} 折线图数据
   */
  toRoundLineChart(apiData) {
    return toLineChartData(apiData, {
      xAxisKey: 'roundIndex',
      valueKey: 'meanReward',
      seriesName: '平均奖励',
      title: '版本轮次奖励趋势'
    })
  }
}

/**
 * 评估记录模块特定格式化函数
 */
export const recordsFormatter = {
  /**
   * 将评分数据转换为柱状图格式
   * @param {Object} apiData - API数据
   * @returns {Object} 柱状图数据
   */
  toScoresBarChart(apiData) {
    return toBarChartData(apiData, {
      xAxisKey: 'name',
      valueKey: 'value',
      seriesName: '平均分数',
      title: '评分指标对比'
    })
  },

  /**
   * 将评估结果数据转换为饼图格式
   * @param {Object} apiData - API数据
   * @returns {Object} 饼图数据
   */
  toResultPieChart(apiData) {
    const resultMap = {
      'pass': '通过',
      'fail': '失败',
      'pending': '待评估'
    }

    const formattedData = extractData(apiData).map(item => ({
      ...item,
      name: resultMap[item.name] || item.name
    }))

    return toPieChartData({
      ...apiData,
      data: formattedData
    }, {
      title: '评估结果分布'
    })
  },

  /**
   * 将评分雷达数据转换为柱状图格式
   * @param {Object} apiData - API数据
   * @returns {Object} 柱状图数据
   */
  toScoreRadarBarChart(apiData) {
    return toBarChartData(apiData, {
      xAxisKey: 'name',
      valueKey: 'value',
      seriesName: '平均分',
      title: '各评分维度平均值'
    })
  },

}

/**
 * 根据模块和统计类型选择相应的格式化函数
 * @param {string} module - 模块名称
 * @param {string} statType - 统计类型
 * @returns {Function|null} 格式化函数
 */
export function getFormatter(module, statType) {
  const formatterMap = {
    experiments: {
      'byStatus': experimentsFormatter.toStatusPieChart,
      'byDomain': experimentsFormatter.toDomainBarChart
    },
    metrics: {
      'byTimeline': metricsFormatter.toTimelineChart
    },
    versions: {
      'byRound': versionsFormatter.toRoundLineChart
    },
    records: {
      'byScores': recordsFormatter.toScoresBarChart,
      'byResult': recordsFormatter.toResultPieChart,
      'byScoreRadar': recordsFormatter.toScoreRadarBarChart
    }
  }

  return formatterMap[module]?.[statType] || null
}

/**
 * 自动格式化统计数据
 * @param {string} module - 模块名称
 * @param {string} statType - 统计类型
 * @param {Object} apiData - API返回的数据
 * @param {string} chartType - 图表类型（pie/bar/line）
 * @returns {Object} 格式化后的图表数据
 */
export function autoFormatStats(module, statType, apiData, chartType) {
  const formatter = getFormatter(module, statType)

  if (formatter) {
    // 使用特定格式化函数
    return formatter(apiData)
  }

  // 使用通用格式化函数
  switch (chartType) {
    case 'pie':
      return toPieChartData(apiData)
    case 'bar':
      return toBarChartData(apiData)
    case 'line':
      return toLineChartData(apiData)
    default:
      // 默认使用饼图格式
      return toPieChartData(apiData)
  }
}

export default {
  toPieChartData,
  toBarChartData,
  toLineChartData,
  experimentsFormatter,
  metricsFormatter,
  versionsFormatter,
  recordsFormatter,
  getFormatter,
  autoFormatStats
}