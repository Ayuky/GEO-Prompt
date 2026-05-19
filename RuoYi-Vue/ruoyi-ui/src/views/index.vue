<template>
  <div class="app-container home">
    <el-row :gutter="20">
      <el-col :sm="24" :lg="24" style="padding-left: 20px">
        <h2>GEO Prompt 优化系统</h2>
        <p class="intro-text">
          GEO Prompt 优化系统是一个智能化的提示词优化与管理平台，专注于提升大语言模型（LLM）在地理信息相关任务中的表现。
          系统集成了实验管理、模型训练、效果评估等核心功能，帮助开发者快速迭代和优化提示词策略。
        </p>
        
        <el-divider />
        
        <h3>核心功能</h3>
        <el-row :gutter="20" class="feature-row">
          <el-col :xs="24" :sm="12" :md="8" class="feature-item">
            <el-card shadow="hover">
              <div class="feature-icon">🧪</div>
              <h4>实验管理</h4>
              <p>创建和管理实验，追踪不同提示词的优化效果，支持 A/B 测试和多版本对比</p>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8" class="feature-item">
            <el-card shadow="hover">
              <div class="feature-icon">🤖</div>
              <h4>模型训练</h4>
              <p>基于强化学习的提示词自动优化，支持自定义奖励函数和训练策略</p>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8" class="feature-item">
            <el-card shadow="hover">
              <div class="feature-icon">📊</div>
              <h4>效果评估</h4>
              <p>多维度评估指标体系，实时监控模型表现，可视化展示优化成果</p>
            </el-card>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" class="feature-row">
          <el-col :xs="24" :sm="12" :md="8" class="feature-item">
            <el-card shadow="hover">
              <div class="feature-icon">🔄</div>
              <h4>Prompt控制</h4>
              <p>完整的提示词管理，支持差异对比和历史追溯</p>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8" class="feature-item">
            <el-card shadow="hover">
              <div class="feature-icon">🎯</div>
              <h4>智能推荐</h4>
              <p>基于历史数据的智能推荐引擎，自动建议最优提示词配置</p>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8" class="feature-item">
            <el-card shadow="hover">
              <div class="feature-icon">🔗</div>
              <h4>Langfuse 集成</h4>
              <p>深度集成 Langfuse 可观测性平台，实现完整的链路追踪和性能监控</p>
            </el-card>
          </el-col>
        </el-row>
        
        <el-divider />
        
        <h3>技术架构</h3>
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :lg="6">
            <h4>后端技术栈</h4>
            <ul class="tech-list">
              <li><el-tag size="small" type="success">Python</el-tag> FastAPI</li>
              <li><el-tag size="small" type="primary">SQLAlchemy</el-tag> ORM</li>
              <li><el-tag size="small" type="warning">Pydantic</el-tag> 数据验证</li>
              <li><el-tag size="small" type="danger">Langfuse</el-tag> 可观测性</li>
            </ul>
          </el-col>
          
          <el-col :xs="24" :sm="12" :lg="6">
            <h4>前端技术栈</h4>
            <ul class="tech-list">
              <li><el-tag size="small" type="success">Vue.js</el-tag> 渐进式框架</li>
              <li><el-tag size="small" type="primary">Element UI</el-tag> 组件库</li>
              <li><el-tag size="small" type="warning">Vuex</el-tag> 状态管理</li>
              <li><el-tag size="small" type="danger">Axios</el-tag> HTTP 客户端</li>
            </ul>
          </el-col>
          
          <el-col :xs="24" :sm="12" :lg="6">
            <h4>AI/ML 技术</h4>
            <ul class="tech-list">
              <li><el-tag size="small" type="success">RL</el-tag> 强化学习</li>
              <li><el-tag size="small" type="primary">LLM</el-tag> 大语言模型</li>
              <li><el-tag size="small" type="warning">Prompt Eng</el-tag> 提示工程</li>
              <li><el-tag size="small" type="danger">Reward Model</el-tag> 奖励模型</li>
            </ul>
          </el-col>
          
          <el-col :xs="24" :sm="12" :lg="6">
            <h4>基础设施</h4>
            <ul class="tech-list">
              <li><el-tag size="small" type="success">Docker</el-tag> 容器化</li>
              <li><el-tag size="small" type="primary">PostgreSQL</el-tag> 数据库</li>
              <li><el-tag size="small" type="warning">Redis</el-tag> 缓存</li>
              <li><el-tag size="small" type="danger">Nginx</el-tag> 反向代理</li>
            </ul>
          </el-col>
        </el-row>
        
        <el-divider />
        
        <h3>应用场景</h3>
        <el-alert
          title="提示词自动化调优"
          type="success"
          :closable="false"
          description="通过强化学习算法自动迭代和优化提示词，减少人工试错成本，快速找到最优配置"
          show-icon
          style="margin-bottom: 15px"
        />
        <el-alert
          title="模型效果监控与分析"
          type="warning"
          :closable="false"
          description="实时监控提示词执行效果，多维度数据分析，为持续优化提供数据支撑"
          show-icon
          style="margin-bottom: 15px"
        />
        
        <el-divider />
        
        <p class="version-info">
          <b>当前版本:</b> <span>v1.0.0</span> | 
          <b>系统状态:</b> <el-tag size="small" type="success">运行中</el-tag>
        </p>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: "Index",
  data() {
    return {
      version: "1.0.0"
    }
  },
  methods: {
    goTarget(href) {
      window.open(href, "_blank")
    }
  }
}
</script>

<style scoped lang="scss">
.home {
  blockquote {
    padding: 10px 20px;
    margin: 0 0 20px;
    font-size: 17.5px;
    border-left: 5px solid #eee;
  }
  
  .intro-text {
    font-size: 15px;
    line-height: 1.8;
    color: #606266;
    margin: 20px 0;
  }
  
  h2 {
    margin-top: 10px;
    font-size: 28px;
    font-weight: 600;
    color: #303133;
  }
  
  h3 {
    margin: 25px 0 15px 0;
    font-size: 22px;
    font-weight: 500;
    color: #303133;
  }
  
  h4 {
    margin-top: 0px;
    margin-bottom: 15px;
    font-size: 16px;
    font-weight: 500;
    color: #606266;
  }
  
  p {
    margin-top: 10px;
    line-height: 1.6;

    b {
      font-weight: 700;
    }
  }
  
  .feature-row {
    margin: 20px 0;
  }
  
  .feature-item {
    margin-bottom: 20px;
    
    .feature-icon {
      font-size: 40px;
      text-align: center;
      margin-bottom: 10px;
    }
    
    h4 {
      text-align: center;
      margin: 10px 0;
    }
    
    p {
      text-align: center;
      font-size: 13px;
      color: #909399;
      margin: 10px 0;
    }
  }
  
  .tech-list {
    padding: 0;
    margin: 0;
    list-style-type: none;
    
    li {
      padding: 8px 0;
      font-size: 14px;
      color: #606266;
      
      .el-tag {
        margin-right: 8px;
      }
    }
  }
  
  .version-info {
    text-align: center;
    padding: 20px 0;
    font-size: 14px;
    color: #909399;
  }
  
  ::v-deep .el-card {
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-5px);
    }
    
    .el-card__body {
      padding: 20px;
    }
  }
  
  ::v-deep .el-divider {
    margin: 30px 0;
  }
  
  ::v-deep .el-alert {
    margin-bottom: 15px;
  }
}
</style>