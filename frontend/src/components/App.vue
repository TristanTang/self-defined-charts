<script setup lang="ts">
import { ref, onMounted, computed } from 'vue' // 新增：导入 computed
import axios from 'axios'
import * as echarts from 'echarts'

// 类型定义
interface Column {
  column_name: string
  column_name_cn: string
}

interface Table {
  table_name: string
  table_name_cn: string
  columns: Column[]
}

// 状态管理
const tables = ref<Table[]>([])
const selectedTable = ref('')
const selectedColumn = ref('')
const statisticFunction = ref('SUM')
const groupColumn = ref('')
const chartType = ref(1)
const chartInstance = ref<echarts.ECharts | null>(null)
const chartContainer = ref<HTMLElement | null>(null)

// 获取表结构
const loadTables = async () => {
  try {
    console.log("loadTables", "开始调用接口")
    const res = await axios.get('/api/tables')
    console.log("loadTables", "调用完毕", res.data)
    
    // 验证数据结构，避免运行时错误
    if (res.data && Array.isArray(res.data.tables)) {
      tables.value = res.data.tables
      console.log("tables.value", tables.value)
      
      if (tables.value.length > 0) {
        selectedTable.value = tables.value[0].table_name
      }
    } else {
      console.error("接口返回数据格式不正确", res.data)
      tables.value = []
    }
  } catch (error) {
    console.error("加载表结构失败", error)
    tables.value = [] // 清空旧数据以避免显示过期或错误的数据
  }
}

// 根据选中的表获取字段
const getAvailableColumns = () => {
  const table = tables.value.find(t => t.table_name === selectedTable.value)
  return table ? table.columns : []
}

// 新增分组字段的默认选项
const groupOptions = computed(() => {
  const columns = getAvailableColumns()
  return [{ column_name: '', column_name_cn: '不分组' }, ...columns]
})

// 新增方法：根据图表类型和业务数据生成 option 配置
const buildChartOption = (chartType: number, data: { labels: string[], values: number[] }) => {
  switch (chartType) {
    case 1: // 柱状图
      return {
        xAxis: {
          type: 'category',
          data: data.labels
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            data: data.values,
            type: 'bar'
          }
        ]
      }
    case 2: // 饼图
      return {

      //  title: {
      //    text: '数据分布',
      //    subtext: '统计结果',
      //    left: 'center'
      //  },

        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: '数据分布',
            type: 'pie',
            radius: '50%',
            data: data.labels.map((label, index) => ({ name: label, value: data.values[index] }))
          }
        ]
      }
    case 3: // 折线图
      return {
        xAxis: {
          type: 'category',
          data: data.labels
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            data: data.values,
            type: 'line'
          }
        ]
      }
    default:
      throw new Error('Unsupported chart type')
  }
}

// 提交统计
const submitStatistics = async () => {
  if (!selectedTable.value || !selectedColumn.value) return

  const params = {
    table_name: selectedTable.value,
    statistic_column_name: selectedColumn.value,
    statistic_function: statisticFunction.value,
    group_column_name: groupColumn.value,
    echart_type: chartType.value
  }

  const res = await axios.post('/api/submit_statistics', params)

  if (chartInstance.value && res.data.code === 0) {
    console.log("submit statistics res", res)
    chartInstance.value.clear()

    // 调用 buildChartOption 方法生成 option 配置
    const option = buildChartOption(chartType.value, res.data.data)
    chartInstance.value.setOption(option)
  }
}

// 初始化图表
onMounted(() => {
  chartInstance.value = echarts.init(chartContainer.value!)
  loadTables()
})
</script>

<template>
  <div class="container">
    <!-- 区域1：统计条件 -->
    <div class="controls">
      <a-row :gutter="16">
        <a-col :span="12">
          <label>数据表：</label>
          <a-select v-model:value="selectedTable" style="width: 200px" @change="selectedColumn = ''">
            <a-select-option v-for="table in tables" :key="table.table_name" :value="table.table_name">
              {{ table.table_name_cn }}
            </a-select-option>
          </a-select>
        </a-col>

        <a-col :span="12">
          <label>字段名：</label>
          <a-select v-model:value="selectedColumn" style="width: 200px">
            <a-select-option v-for="col in getAvailableColumns()" :key="col.column_name" :value="col.column_name">
              {{ col.column_name_cn }}
            </a-select-option>
          </a-select>
        </a-col>

        <a-col :span="12">
          <label>统计方法：</label>
          <a-select v-model:value="statisticFunction" style="width: 200px">
            <a-select-option v-for="func in ['SUM','AVG','COUNT']" :key="func" :value="func">
              {{ func }}
            </a-select-option>
          </a-select>
        </a-col>

        <a-col :span="12">
          <label>分组字段：</label>
          <a-select v-model:value="groupColumn" style="width: 200px">
            <a-select-option v-for="col in groupOptions" :key="col.column_name" :value="col.column_name">
              {{ col.column_name_cn }}
            </a-select-option>
          </a-select>
        </a-col>

        <a-col :span="12">
          <label>图表类型：</label>
          <a-select v-model:value="chartType" style="width: 200px">
            <a-select-option v-for="[val,label] in [[1,'柱状图'],[2,'饼图'],[3,'折线图']]" :key="val" :value="val">
              {{ label }}
            </a-select-option>
          </a-select>
        </a-col>

        <a-col :span="24">
          <a-button type="primary" @click="submitStatistics">提交统计</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 区域2：图表展示 -->
    <div class="chart-container" ref="chartContainer" style="width: 100%; height: 600px;"></div>
  </div>
</template>

<style scoped>
.container {
  padding: 20px;
}
.controls {
  margin-bottom: 20px;
}
label {
  display: inline-block;
  width: 80px;
  margin-right: 10px;
}
</style>