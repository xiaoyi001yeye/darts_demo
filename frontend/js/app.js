// 全局变量
const API_BASE_URL = '/api';  // 使用相对路径，通过 Nginx 代理到后端
let isLoading = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('时间序列预测系统启动...');
    initializeApp();
});

// 初始化应用
async function initializeApp() {
    try {
        await loadAvailableModels();
        await loadDataInfo();  // 加载数据信息
        initializeChart();
        setupEventListeners();
        initializeDateRangeControls(); // 初始化时间范围控件
        showMessage('系统初始化完成', 'success');
    } catch (error) {
        console.error('初始化失败:', error);
        showMessage('系统初始化失败: ' + error.message, 'error');
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 模型选择变化
    document.getElementById('modelSelect').addEventListener('change', function() {
        const selectedModel = this.value;
        if (selectedModel) {
            updateModelDescription(selectedModel);
            loadModelParameters(selectedModel);  // 加载模型参数配置
        } else {
            clearModelParameters();  // 清除参数配置
        }
    });
    
    // 键盘快捷键
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey && event.key === 'Enter') {
            runForecast();
        }
    });
    
}

// 加载模型参数配置
async function loadModelParameters(modelId) {
    try {
        const response = await fetch(`${API_BASE_URL}/model/${modelId}/parameters`);
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const data = await response.json();
        displayModelParameters(data.parameters);
    } catch (error) {
        console.error('加载模型参数失败:', error);
        clearModelParameters();
    }
}

// 显示模型参数配置
function displayModelParameters(parameters) {
    const container = document.getElementById('modelParametersContainer');
    if (!container) return;
    
    let html = '<div class="parameters-grid">';
    
    for (const [key, param] of Object.entries(parameters)) {
        html += `
            <div class="control-group">
                <label for="param_${key}">
                    <i class="fas fa-sliders-h"></i> ${key}
                </label>
        `;
        
        if (param.type === 'select') {
            html += `<select id="param_${key}" class="form-control">`;
            param.options.forEach(option => {
                const value = option === null ? 'none' : option;
                const display = option === null ? '无' : option;
                const selected = option === param.default ? 'selected' : '';
                html += `<option value="${value}" ${selected}>${display}</option>`;
            });
            html += `</select>`;
        } else {
            const value = param.default !== undefined ? param.default : '';
            const min = param.min !== undefined ? `min="${param.min}"` : '';
            const max = param.max !== undefined ? `max="${param.max}"` : '';
            html += `<input type="number" id="param_${key}" class="form-control" value="${value}" ${min} ${max}>`;
        }
        
        html += `<small class="help-text">${param.description || ''}</small>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
    container.style.display = 'block';
}

// 清除模型参数配置
function clearModelParameters() {
    const container = document.getElementById('modelParametersContainer');
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}

// 获取模型参数值
function getModelParameters() {
    const container = document.getElementById('modelParametersContainer');
    if (!container || container.style.display === 'none') {
        return {};
    }
    
    const parameters = {};
    const inputs = container.querySelectorAll('input, select');
    
    inputs.forEach(input => {
        const key = input.id.replace('param_', '');
        if (input.type === 'number') {
            parameters[key] = parseFloat(input.value) || 0;
        } else {
            parameters[key] = input.value === 'none' ? null : input.value;
        }
    });
    
    // 添加时间范围参数
    const dataStartDate = document.getElementById('dataStartDate').value;
    const dataEndDate = document.getElementById('dataEndDate').value;
    
    if (dataStartDate) parameters.data_start_date = dataStartDate;
    if (dataEndDate) parameters.data_end_date = dataEndDate;
    
    return parameters;
}

// 运行预测
async function runForecast() {
    if (isLoading) {
        showMessage('预测正在进行中，请稍候...', 'warning');
        return;
    }
    
    const model = document.getElementById('modelSelect').value;
    const periods = document.getElementById('periodsInput').value;

    // 参数验证
    if (!model) {
        showMessage('请选择预测模型', 'warning');
        return;
    }
    
    if (!periods || parseInt(periods) <= 0 || parseInt(periods) > 365) {
        showMessage('请输入有效的预测周期 (1-365天)', 'warning');
        return;
    }
    
    try {
        isLoading = true;
        showLoading('正在运行预测分析...');
        updateForecastButton(true);
        
        // 获取模型参数
        const modelParams = getModelParameters();
        
        const requestData = {
            model: model,
            periods: parseInt(periods),
            ...modelParams  // 展开模型参数
        };
        
        console.log('发送预测请求:', requestData);
        
        const response = await fetch(`${API_BASE_URL}/forecast`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP错误: ${response.status}`);
        }
        
        let data = await response.json();
        console.log('预测结果:', data);
        //data 转为json格式
        if (typeof data === 'string') {
            data = JSON.parse(data);
        }
        // 更新图表
        updateChart(data);
        
        // 更新评估指标
        updateMetrics(data.metrics);
        
        // 更新模型信息
//        updateModelInfo(data.model_info);
        
        showMessage('预测完成！', 'success');
        
    } catch (error) {
        console.error('预测失败:', error);
        showMessage('预测失败: ' + error.message, 'error');
    } finally {
        isLoading = false;
        hideLoading();
        updateForecastButton(false);
    }
}

// 加载可用模型
async function loadAvailableModels() {
    try {
        showLoading('加载模型列表...');
        
        const response = await fetch(`${API_BASE_URL}/models`);
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const models = await response.json();
        
        const select = document.getElementById('modelSelect');
        select.innerHTML = '<option value="">选择预测模型...</option>';
        
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            option.setAttribute('data-description', model.description || '');
            select.appendChild(option);
        });
        
        hideLoading();
        console.log('模型列表加载完成:', models);
        
    } catch (error) {
        hideLoading();
        console.error('加载模型失败:', error);
        showMessage('加载模型列表失败: ' + error.message, 'error');
    }
}

// 获取并显示数据信息
async function loadDataInfo() {
    try {
        showLoading('加载数据信息...');
        
        // 获取数据基本信息
        const infoResponse = await fetch(`${API_BASE_URL}/data/info`);
        if (!infoResponse.ok) {
            throw new Error(`HTTP错误: ${infoResponse.status}`);
        }
        
        const infoResult = await infoResponse.json();
        
        if (infoResult.status === 'success') {
            displayDataInfo(infoResult.data);
        } else {
            throw new Error(infoResult.message);
        }
        
        // 获取数据预览
        const previewResponse = await fetch(`${API_BASE_URL}/data/preview2`);
        if (!previewResponse.ok) {
            throw new Error(`HTTP错误: ${previewResponse.status}`);
        }
        
        const previewResult = await previewResponse.json();
        
        if (previewResult.status === 'success') {
            displayDataPreview(previewResult.data);
        } else {
            throw new Error(previewResult.message);
        }
        
    } catch (error) {
        console.error('加载数据信息失败:', error);
        showMessage('加载数据信息失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// 显示数据信息
function displayDataInfo(dataInfo) {
    document.getElementById('deviceId').textContent = dataInfo.device_id || '-';
    document.getElementById('totalPoints').textContent = dataInfo.total_points || '-';
    document.getElementById('frequency').textContent = dataInfo.frequency || '-';
    
    if (dataInfo.date_range) {
        document.getElementById('timeRange').textContent = 
            `${dataInfo.date_range.start} 至 ${dataInfo.date_range.end}`;
    } else {
        document.getElementById('timeRange').textContent = '-';
    }
    
    if (dataInfo.statistics) {
        document.getElementById('meanValue').textContent = 
            dataInfo.statistics.mean ? dataInfo.statistics.mean.toFixed(2) : '-';
        document.getElementById('stdValue').textContent = 
            dataInfo.statistics.std ? dataInfo.statistics.std.toFixed(2) : '-';
    } else {
        document.getElementById('meanValue').textContent = '-';
        document.getElementById('stdValue').textContent = '-';
    }
}

// 显示数据预览 - 根据新逻辑重写
function displayDataPreview(previewData) {
    const tbody = document.getElementById('previewTableBody');
    
    if (!previewData.records || previewData.records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">暂无数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    previewData.records.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.data_start_time || '-'}</td>
            <td>${item.data_end_time || '-'}</td>
            <td>${item.ci_id || '-'}</td>
            <td>${item.ci_type || '-'}</td>
            <td>${item.code || '-'}</td>
            <td>${item.normal_count !== undefined ? item.normal_count : '-'}</td>
            <td>${item.abnormal_count !== undefined ? item.abnormal_count : '-'}</td>
        `;
        tbody.appendChild(tr);
    });
}

// 上传文件
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        return;
    }
    
    if (!file.name.endsWith('.csv')) {
        showMessage('只支持CSV格式文件', 'warning');
        return;
    }
    
    try {
        showLoading('上传数据文件...');
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `上传失败: ${response.status}`);
        }
        
        const result = await response.json();
        
        // 显示上传状态
        showUploadStatus(result);
        
        // 预览数据
        await previewUploadedData();
        
        showMessage('数据上传成功！', 'success');
        
    } catch (error) {
        console.error('上传失败:', error);
        showMessage('上传失败: ' + error.message, 'error');
    } finally {
        hideLoading();
        // 清空文件输入
        fileInput.value = '';
    }
}

// 预览上传的数据
async function previewUploadedData() {
    try {
        const response = await fetch(`${API_BASE_URL}/data/preview`);
        if (!response.ok) {
            return;
        }
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // 在图表中显示预览数据
            updateChart({
                historical: {
                    dates: result.data.data.map(item => item.time),
                    values: result.data.data.map(item => item.value)
                },
                forecast: { dates: [], values: [] },
                validation: { dates: [], values: [] }
            });
        }
        
    } catch (error) {
        console.error('预览数据失败:', error);
    }
}

// 显示上传状态
function showUploadStatus(result) {
    const statusSection = document.getElementById('uploadStatus');
    const infoElement = document.getElementById('uploadInfo');
    
    if (result.rows && result.date_range) {
        infoElement.innerHTML = `
            <strong>数据行数：</strong>${result.rows} 行<br>
            <strong>时间范围：</strong>${result.date_range.start} 至 ${result.date_range.end}
        `;
        statusSection.style.display = 'block';
        
        // 5秒后自动隐藏
        setTimeout(() => {
            statusSection.style.display = 'none';
        }, 5000);
    }
}

// 更新评估指标显示
function updateMetrics(metrics) {
    const container = document.getElementById('metricsContainer');
    
    if (!metrics || (!metrics.mape && !metrics.rmse && !metrics.mae)) {
        container.innerHTML = `
            <div class="metrics-placeholder">
                <i class="fas fa-info-circle"></i>
                <p>无法计算评估指标（验证数据不足）</p>
            </div>
        `;
        return;
    }
    
    // 评估指标的说明
    const getMetricStatus = (value, type) => {
        let status = 'good';
        let description = '';
        
        switch(type) {
            case 'mape':
                if (value > 20) status = 'poor';
                else if (value > 10) status = 'fair';
                description = value <= 10 ? '预测精度很好' : value <= 20 ? '预测精度一般' : '预测精度较差';
                break;
            case 'direction_accuracy':
                if (value < 0.5) status = 'poor';
                else if (value < 0.7) status = 'fair';
                description = value >= 0.7 ? '趋势预测很好' : value >= 0.5 ? '趋势预测一般' : '趋势预测较差';
                break;
        }
        
        return { status, description };
    };
    
    container.innerHTML = `
        <div class="metrics-grid">
            ${metrics.mape ? `
                <div class="metric-card ${getMetricStatus(metrics.mape, 'mape').status}">
                    <div class="metric-header">
                        <i class="fas fa-percentage"></i>
                        <h4>MAPE</h4>
                    </div>
                    <div class="metric-value">${metrics.mape.toFixed(2)}%</div>
                    <div class="metric-description">平均绝对百分比误差</div>
                    <div class="metric-status">${getMetricStatus(metrics.mape, 'mape').description}</div>
                </div>
            ` : ''}
            
            ${metrics.rmse ? `
                <div class="metric-card">
                    <div class="metric-header">
                        <i class="fas fa-square-root-alt"></i>
                        <h4>RMSE</h4>
                    </div>
                    <div class="metric-value">${metrics.rmse.toFixed(2)}</div>
                    <div class="metric-description">均方根误差</div>
                </div>
            ` : ''}
            
            ${metrics.mae ? `
                <div class="metric-card">
                    <div class="metric-header">
                        <i class="fas fa-ruler"></i>
                        <h4>MAE</h4>
                    </div>
                    <div class="metric-value">${metrics.mae.toFixed(2)}</div>
                    <div class="metric-description">平均绝对误差</div>
                </div>
            ` : ''}
            
            ${metrics.direction_accuracy ? `
                <div class="metric-card ${getMetricStatus(metrics.direction_accuracy, 'direction_accuracy').status}">
                    <div class="metric-header">
                        <i class="fas fa-trending-up"></i>
                        <h4>方向准确率</h4>
                    </div>
                    <div class="metric-value">${(metrics.direction_accuracy * 100).toFixed(1)}%</div>
                    <div class="metric-description">趋势方向预测准确度</div>
                    <div class="metric-status">${getMetricStatus(metrics.direction_accuracy, 'direction_accuracy').description}</div>
                </div>
            ` : ''}
        </div>
    `;
}

// 更新预测信息
function updateForecastInfo(forecastInfo) {
    // 可以在控制台显示预测信息或添加到页面某个位置
    console.log('预测信息:', forecastInfo);
}

// 更新训练按钮状态
function updateTrainButton(loading) {
    const btn = document.getElementById('trainBtn');
    if (!btn) return;
    
    if (loading) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 训练中...';
        btn.disabled = true;
        btn.classList.add('loading');
    } else {
        btn.innerHTML = '<i class="fas fa-play"></i> 训练模型';
        btn.disabled = false;
        btn.classList.remove('loading');
    }
}

// 更新预测按钮状态
function updatePredictButton(loading) {
    const btn = document.getElementById('predictBtn');
    if (!btn) return;
    
    if (loading) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 预测中...';
        btn.disabled = true;
        btn.classList.add('loading');
    } else {
        btn.innerHTML = '<i class="fas fa-crystal-ball"></i> 运行预测';
        btn.disabled = isModelTrained ? false : true;
        btn.classList.remove('loading');
    }
}

// 更新模型描述
function updateModelDescription(modelId) {
    const select = document.getElementById('modelSelect');
    const selectedOption = select.querySelector(`option[value="${modelId}"]`);
    
    if (selectedOption) {
        const description = selectedOption.getAttribute('data-description');
        // 可以在这里显示模型描述，例如在一个提示框中
        console.log('模型描述:', description);
    }
}

// 更新预测按钮状态
function updateForecastButton(loading) {
    const btn = document.getElementById('forecastBtn');
    
    if (loading) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 预测中...';
        btn.disabled = true;
        btn.classList.add('loading');
    } else {
        btn.innerHTML = '<i class="fas fa-play"></i> 运行预测';
        btn.disabled = false;
        btn.classList.remove('loading');
    }
}

// 显示加载状态
function showLoading(message = '加载中...') {
    const overlay = document.getElementById('loadingOverlay');
    const messageElement = overlay.querySelector('p');
    messageElement.textContent = message;
    overlay.style.display = 'flex';
}

// 隐藏加载状态
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'none';
}

// 显示消息提示
function showMessage(message, type = 'info') {
    const container = document.getElementById('messageContainer');
    
    const messageElement = document.createElement('div');
    messageElement.className = `message message-${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    messageElement.innerHTML = `
        <i class="fas ${icons[type] || icons.info}"></i>
        <span>${message}</span>
        <button class="message-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    container.appendChild(messageElement);
    
    // 自动移除消息
    setTimeout(() => {
        if (messageElement.parentElement) {
            messageElement.remove();
        }
    }, 5000);
}

// 全屏切换
function toggleFullscreen() {
    const chartContainer = document.getElementById('chartContainer');
    
    if (!document.fullscreenElement) {
        chartContainer.requestFullscreen().then(() => {
            // 全屏后需要重新调整图表大小
            if (window.forecastChart) {
                setTimeout(() => {
                    window.forecastChart.resize();
                }, 100);
            }
        }).catch(err => {
            console.error('进入全屏失败:', err);
        });
    } else {
        document.exitFullscreen();
    }
}

// 下载图表
function downloadChart() {
    if (window.forecastChart) {
        const url = window.forecastChart.getDataURL({
            type: 'png',
            pixelRatio: 2,
            backgroundColor: '#fff'
        });
        
        const link = document.createElement('a');
        link.download = `时间序列预测_${new Date().toISOString().slice(0, 10)}.png`;
        link.href = url;
        link.click();
    } else {
        showMessage('没有可下载的图表', 'warning');
    }
}

// 显示帮助
function showHelp() {
    document.getElementById('helpModal').style.display = 'flex';
}

// 显示关于
function showAbout() {
    document.getElementById('aboutModal').style.display = 'flex';
}

// 关闭模态框
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// 点击模态框外部关闭
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

// 窗口大小变化时调整图表
window.addEventListener('resize', function() {
    if (window.forecastChart) {
        window.forecastChart.resize();
    }
});

// 初始化时间范围控件
function initializeDateRangeControls() {
    // 从数据信息中获取默认时间范围
    const timeRangeElement = document.getElementById('timeRange');
    if (timeRangeElement && timeRangeElement.textContent !== '-') {
        const timeRangeText = timeRangeElement.textContent;
        const [startDateStr, endDateStr] = timeRangeText.split(' 至 ');
        
        if (startDateStr && endDateStr) {
            // 设置日期控件的值，使用value而不是valueAsDate
            document.getElementById('dataStartDate').value = startDateStr.split(' ')[0]; // 只取日期部分
            document.getElementById('dataEndDate').value = endDateStr.split(' ')[0]; // 只取日期部分
        }
    } else {
        // 如果没有数据信息，则设置默认值（最近一年）
        const today = new Date();
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        // 格式化为 YYYY-MM-DD
        const formatDate = (date) => {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        };
        
        document.getElementById('dataStartDate').value = formatDate(oneYearAgo);
        document.getElementById('dataEndDate').value = formatDate(today);
    }
}
