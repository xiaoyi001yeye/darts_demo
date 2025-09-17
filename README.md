# 🚀 时间序列预测系统

基于 Python Darts 库的前后端分离时间序列预测系统，提供智能化的时间序列分析与预测功能。

## ✨ 系统特性

- 🧠 **多种预测模型**：支持指数平滑、Prophet、ARIMA、Four Theta 等多种算法
- 📊 **实时可视化**：基于 ECharts 的交互式图表展示
- 📈 **智能评估**：自动计算 MAPE、RMSE、MAE 等评估指标
- 📁 **数据上传**：支持 CSV 格式数据文件上传
- 🌐 **前后端分离**：Flask 后端 + HTML/JavaScript 前端
- 📱 **响应式设计**：适配不同屏幕尺寸的设备

## 🏗️ 项目结构

```
darts_demo/
├── backend/                 # 后端代码
│   ├── app.py              # Flask 主应用
│   ├── utils.py            # 工具函数
│   ├── models/             # 模型存储目录
│   ├── data/               # 数据存储目录
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端代码
│   ├── index.html          # 主页面
│   ├── css/
│   │   └── style.css       # 样式文件
│   └── js/
│       ├── app.js          # 前端主逻辑
│       └── charts.js       # 图表渲染逻辑
├── Theta.py                # 原有的 Theta 模型示例
├── ck_time_series_forecast.py  # ClickHouse 集成示例
└── README.md               # 项目说明
```

## 🛠️ 安装和运行

### 环境要求

- Python 3.8+
- pip
- 现代浏览器（支持 ES6）

### 1. 安装后端依赖

```bash
# 激活您现有的虚拟环境
source darts-env/bin/activate  # Linux/Mac
# 或
# darts-env\Scripts\activate    # Windows

# 安装依赖
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
python app.py
```

后端服务将在 `http://localhost:5000` 启动。

### 3. 启动前端服务

```bash
# 在另一个终端窗口中
cd frontend
python -m http.server 8080
```

或者使用 Node.js 的 http-server：

```bash
npx http-server -p 8080
```

前端页面将在 `http://localhost:8080` 可用。

## 🎯 使用指南

### 快速开始

1. **打开系统**：在浏览器中访问 `http://localhost:8080`
2. **选择模型**：从下拉菜单中选择预测模型
3. **设置参数**：输入预测周期（天数）
4. **运行预测**：点击"运行预测"按钮
5. **查看结果**：在图表中查看预测结果和评估指标

### 模型说明

| 模型 | 适用场景 | 特点 |
|------|----------|------|
| **指数平滑** | 有趋势和季节性的数据 | 计算快速，适合短期预测 |
| **Prophet** | 缺失数据、节假日影响 | Facebook 开发，鲁棒性强 |
| **ARIMA** | 平稳时间序列 | 经典统计模型，可解释性强 |
| **Four Theta** | 短期预测 | 简单有效，适合快速预测 |

### 数据上传

- 支持 CSV 格式文件
- 需要包含时间列和数值列
- 时间格式：`YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`
- 示例数据格式：

```csv
time,value
2023-01-01,100.5
2023-01-02,102.3
2023-01-03,98.7
...
```

## 📊 API 接口

### 后端 API

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/models` | GET | 获取可用模型列表 |
| `/api/forecast` | POST | 执行预测 |
| `/api/upload` | POST | 上传数据文件 |
| `/api/data/preview` | GET | 预览上传的数据 |

### 预测请求示例

```json
{
  "model": "exponential_smoothing",
  "periods": 30,
  "multivariate": false
}
```

### 预测响应示例

```json
{
  "historical": {
    "dates": ["2023-01-01", "2023-01-02", ...],
    "values": [100.5, 102.3, ...]
  },
  "forecast": {
    "dates": ["2023-02-01", "2023-02-02", ...],
    "values": [105.2, 106.8, ...]
  },
  "metrics": {
    "mape": 3.45,
    "rmse": 2.17,
    "mae": 1.89
  },
  "model_info": {
    "type": "exponential_smoothing",
    "train_size": 200,
    "forecast_periods": 30
  }
}
```

## 🔧 技术栈

### 后端

- **Flask**：轻量级 Web 框架
- **Darts**：时间序列预测库
- **Pandas**：数据处理
- **NumPy**：数值计算
- **Scikit-learn**：机器学习工具

### 前端

- **HTML5/CSS3**：页面结构和样式
- **JavaScript (ES6)**：交互逻辑
- **ECharts**：数据可视化
- **Font Awesome**：图标库

## 📝 配置说明

### 后端配置

在 `backend/app.py` 中可以修改：

- 服务器端口：默认 5000
- CORS 设置：允许跨域请求
- 模型参数：各算法的默认参数

### 前端配置

在 `frontend/js/app.js` 中可以修改：

- API 基础地址：`API_BASE_URL`
- 默认预测周期
- 图表主题和样式

## 🚀 扩展功能

### 添加新的预测模型

1. 在 `backend/app.py` 的 `forecast()` 函数中添加新模型
2. 更新 `get_models()` 函数中的模型列表
3. 在前端更新模型选择器

### 集成数据库

可以替换示例数据生成函数，集成：

- PostgreSQL
- MySQL
- ClickHouse
- InfluxDB

### 高级功能

- 模型超参数优化
- 集成学习方法
- 实时数据流预测
- 预测置信区间
- 模型可解释性分析

## 🐛 故障排除

### 常见问题

1. **后端启动失败**
   - 检查 Python 版本（需要 3.8+）
   - 确认依赖已正确安装
   - 检查端口 5000 是否被占用

2. **前端无法访问后端**
   - 确认后端服务已启动
   - 检查 CORS 设置
   - 确认防火墙设置

3. **预测失败**
   - 检查数据格式是否正确
   - 确认预测周期合理（1-365天）
   - 查看浏览器控制台错误信息

4. **文件上传失败**
   - 确认文件格式为 CSV
   - 检查文件大小限制
   - 验证数据列名和格式

### 日志查看

- 后端日志：在运行 `python app.py` 的终端查看
- 前端日志：按 F12 打开浏览器开发者工具查看

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

欢迎提交 Issues 和 Pull Requests！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📞 联系信息

如有问题或建议，请通过以下方式联系：

- 创建 GitHub Issue
- 邮件联系：[your-email@example.com]

## 🙏 致谢

感谢以下开源项目的支持：

- [Darts](https://github.com/unit8co/darts) - 时间序列预测库
- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [ECharts](https://echarts.apache.org/) - 数据可视化
- [Font Awesome](https://fontawesome.com/) - 图标库

---

⭐ 如果这个项目对您有帮助，请给个 Star！