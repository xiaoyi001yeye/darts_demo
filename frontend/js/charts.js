// 图表相关变量
let forecastChart = null;

// 初始化图表
function initializeChart() {
    const chartDom = document.getElementById('chartContainer');
    forecastChart = echarts.init(chartDom, null, {
        renderer: 'canvas',
        useDirtyRect: false
    });
    
    // 设置初始配置
    const option = {
        title: {
            text: '时间序列预测结果',
            left: 'center',
            textStyle: {
                fontSize: 18,
                fontWeight: 'bold',
                color: '#333'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: {
                    backgroundColor: '#6a7985'
                }
            },
            formatter: tooltipFormatter
        },
        legend: {
            data: ['训练数据', '验证数据', '验证预测', '预测数据'],
            top: 40,
            textStyle: {
                fontSize: 12
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '8%',
            top: '15%',
            containLabel: true
        },
        toolbox: {
            feature: {
                saveAsImage: {
                    title: '保存为图片',
                    name: '时间序列预测图'
                },
                dataZoom: {
                    title: {
                        zoom: '区域缩放',
                        back: '还原缩放'
                    }
                },
                restore: {
                    title: '还原'
                }
            },
            right: 20,
            top: 15
        },
        xAxis: {
            type: 'time',
            boundaryGap: false,
            axisLabel: {
                formatter: function (value) {
                    const date = new Date(value);
                    return date.getMonth() + 1 + '/' + date.getDate();
                },
                textStyle: {
                    fontSize: 11
                }
            },
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '数值',
            nameTextStyle: {
                fontSize: 12,
                color: '#666'
            },
            boundaryGap: [0, '20%'],
            axisLabel: {
                formatter: function (value) {
                    return value.toFixed(1);
                },
                textStyle: {
                    fontSize: 11
                }
            },
            axisLine: {
                lineStyle: {
                    color: '#ddd'
                }
            },
            splitLine: {
                lineStyle: {
                    color: '#f0f0f0'
                }
            }
        },
        dataZoom: [
            {
                type: 'inside',
                start: 0,
                end: 100
            },
            {
                type: 'slider',
                start: 0,
                end: 100,
                height: 20,
                bottom: 20
            }
        ],
        series: [
            {
                name: '训练数据',
                type: 'line',
                symbol: 'none',
                sampling: 'lttb',
                lineStyle: {
                    color: '#5470C6',
                    width: 2
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(84, 112, 198, 0.3)' },
                        { offset: 1, color: 'rgba(84, 112, 198, 0.1)' }
                    ])
                },
                data: []
            },
            {
                name: '验证数据',
                type: 'line',
                symbol: 'none',
                lineStyle: {
                    color: '#91CC75',
                    width: 2
                },
                data: []
            },
            {
                name: '验证预测',
                type: 'line',
                symbol: 'circle',
                symbolSize: 3,
                lineStyle: {
                    color: '#91CC75',
                    width: 2,
                    type: 'dashed'
                },
                itemStyle: {
                    color: '#91CC75',
                    borderColor: '#fff',
                    borderWidth: 1
                },
                data: []
            },
            {
                name: '预测数据',
                type: 'line',
                symbol: 'circle',
                symbolSize: 4,
                lineStyle: {
                    color: '#FAC858',
                    width: 3,
                    type: 'dashed'
                },
                itemStyle: {
                    color: '#FAC858',
                    borderColor: '#fff',
                    borderWidth: 2
                },
                data: []
            }
        ],
        animation: true,
        animationDuration: 1000,
        animationEasing: 'cubicOut'
    };
    
    forecastChart.setOption(option);
    
    // 将图表对象暴露到全局，供其他函数使用
    window.forecastChart = forecastChart;
    
    // 响应窗口大小变化
    window.addEventListener('resize', function() {
        if (forecastChart) {
            forecastChart.resize();
        }
    });
    
    // 监听全屏变化
    document.addEventListener('fullscreenchange', function() {
        setTimeout(() => {
            if (forecastChart) {
                forecastChart.resize();
            }
        }, 100);
    });
}

// 更新图表数据
function updateChart(forecastData) {
    try {
        // 添加数据验证
        if (!forecastData || !window.forecastChart) {
            console.error('图表数据或实例不存在');
            return;
        }
        // 从forecastData中提取模型类型生成标题
        let chartTitle = '时间序列预测结果';
        if (forecastData.model_info && forecastData.model_info.type) {
            chartTitle = `${forecastData.model_info.type}模型时间序列预测结果`;
        }

        // 验证并清理数据
        const historicalData = forecastData.historical || { dates: [], values: [] };
        const forecastDataObj = forecastData.forecast || { dates: [], values: [] };
        const validationData = forecastData.validation || { dates: [], values: [] };

        // 日期验证函数
        function isValidDate(dateString) {
            return dateString && !isNaN(new Date(dateString).getTime());
        }

        // 确保日期是有效的
        const cleanHistoricalDates = (historicalData.dates || []).filter(date => isValidDate(date));
        const cleanHistoricalValues = (historicalData.values || []).slice(0, cleanHistoricalDates.length);

        const cleanForecastDates = (forecastDataObj.dates || []).filter(date => isValidDate(date));
        const cleanForecastValues = (forecastDataObj.values || []).slice(0, cleanForecastDates.length);

        const cleanValidationDates = (validationData.dates || []).filter(date => isValidDate(date));
        const cleanValidationValues = (validationData.values || []).slice(0, cleanValidationDates.length);

        // 构建图表数据序列
        const seriesData = [
            {
                name: '历史数据',
                type: 'line',
                data: cleanHistoricalDates.map((date, index) => [
                    new Date(date).getTime(),
                    cleanHistoricalValues[index] !== undefined ? cleanHistoricalValues[index] : null
                ]),
                showSymbol: false,
                smooth: true,
                lineStyle: {
                    width: 2
                }
            }
        ];

        // 只有当预测数据存在时才添加
        if (cleanForecastDates.length > 0 && cleanForecastValues.length > 0) {
            seriesData.push({
                name: '预测数据',
                type: 'line',
                data: cleanForecastDates.map((date, index) => [
                    new Date(date).getTime(),
                    cleanForecastValues[index] !== undefined ? cleanForecastValues[index] : null
                ]),
                showSymbol: false,
                smooth: true,
                lineStyle: {
                    width: 2,
                    type: 'dashed'
                },
                itemStyle: {
                    color: '#FF6B35'
                }
            });
        }

        // 只有当验证数据存在时才添加
        if (cleanValidationDates.length > 0 && cleanValidationValues.length > 0) {
            seriesData.push({
                name: '验证数据',
                type: 'line',
                data: cleanValidationDates.map((date, index) => [
                    new Date(date).getTime(),
                    cleanValidationValues[index] !== undefined ? cleanValidationValues[index] : null
                ]),
                showSymbol: false,
                smooth: true,
                lineStyle: {
                    width: 2,
                    type: 'dotted'
                },
                itemStyle: {
                    color: '#2E7D32'
                }
            });
        }

        // 设置图表选项
        const option = {
            title: {
                text: chartTitle,
                left: 'center',
                textStyle: {
                    fontSize: 16,
                    fontWeight: 'normal'
                }
            },
            tooltip: {
                trigger: 'axis',
                formatter: tooltipFormatter
            },
            legend: {
                data: ['历史数据', '预测数据', '验证数据'].filter(name =>
                    (name === '历史数据') ||
                    (name === '预测数据' && cleanForecastDates.length > 0) ||
                    (name === '验证数据' && cleanValidationDates.length > 0)
                ),
                top: 30
            },
            grid: {
                left: '60',
                right: '40',
                bottom: '60',
                top: '80',
                containLabel: true
            },
            xAxis: {
                type: 'time',
                name: '时间',
                nameLocation: 'middle',
                nameGap: 30
            },
            yAxis: {
                type: 'value',
                name: '数值',
                nameLocation: 'middle',
                nameGap: 40
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    type: 'slider',
                    start: 0,
                    end: 100,
                    bottom: 10
                }
            ],
            series: seriesData
        };

        // 使用配置项更新图表
        window.forecastChart.setOption(option, true);

    } catch (error) {
        console.error('更新图表失败:', error);
        showMessage('图表更新失败: ' + error.message, 'error');
    }
}

// 设置图表主题
function setChartTheme(theme = 'default') {
    if (!forecastChart) return;
    
    const themes = {
        default: {
            backgroundColor: '#fff',
            textColor: '#333',
            lineColors: ['#5470C6', '#91CC75', '#FAC858']
        },
        dark: {
            backgroundColor: '#1e1e1e',
            textColor: '#fff',
            lineColors: ['#6C9BCF', '#95D475', '#FDD85D']
        },
        blue: {
            backgroundColor: '#f8fafe',
            textColor: '#2c3e50',
            lineColors: ['#3498db', '#2ecc71', '#f39c12']
        }
    };
    
    const currentTheme = themes[theme] || themes.default;
    
    forecastChart.setOption({
        backgroundColor: currentTheme.backgroundColor,
        title: {
            textStyle: {
                color: currentTheme.textColor
            }
        },
        legend: {
            textStyle: {
                color: currentTheme.textColor
            }
        },
        xAxis: {
            axisLabel: {
                textStyle: {
                    color: currentTheme.textColor
                }
            }
        },
        yAxis: {
            nameTextStyle: {
                color: currentTheme.textColor
            },
            axisLabel: {
                textStyle: {
                    color: currentTheme.textColor
                }
            }
        },
        series: currentTheme.lineColors.map((color, index) => ({
            lineStyle: { color },
            itemStyle: { color }
        }))
    });
}

// 添加图表标注
function addChartAnnotation(x, y, text, type = 'info') {
    if (!forecastChart) return;
    
    const colors = {
        info: '#409EFF',
        warning: '#E6A23C',
        error: '#F56C6C',
        success: '#67C23A'
    };
    
    forecastChart.setOption({
        graphic: [{
            type: 'circle',
            shape: {
                cx: x,
                cy: y,
                r: 5
            },
            style: {
                fill: colors[type] || colors.info,
                stroke: '#fff',
                lineWidth: 2
            },
            tooltip: {
                formatter: text
            }
        }]
    });
}

// 高亮预测区间
function highlightForecastRegion(forecastStartTime, forecastEndTime) {
    if (!forecastChart) return;
    
    forecastChart.setOption({
        graphic: [{
            type: 'rect',
            shape: {
                x: 0,
                y: 0,
                width: 100,
                height: 100
            },
            style: {
                fill: 'rgba(250, 200, 88, 0.1)',
                stroke: 'rgba(250, 200, 88, 0.3)',
                lineWidth: 1
            }
        }]
    });
}

// 导出图表数据
function exportChartData(format = 'csv') {
    if (!forecastChart) {
        showMessage('没有可导出的图表数据', 'warning');
        return;
    }
    
    const option = forecastChart.getOption();
    const series = option.series;
    
    let data = [];
    let headers = ['时间'];
    
    // 收集所有系列的数据
    series.forEach(s => {
        if (s.data && s.data.length > 0) {
            headers.push(s.name);
        }
    });
    
    // 构建数据行
    const maxLength = Math.max(...series.map(s => s.data ? s.data.length : 0));
    
    for (let i = 0; i < maxLength; i++) {
        const row = [];
        
        // 添加时间
        const firstSeriesWithData = series.find(s => s.data && s.data.length > i);
        if (firstSeriesWithData) {
            row.push(new Date(firstSeriesWithData.data[i][0]).toISOString().split('T')[0]);
        }
        
        // 添加各系列的值
        series.forEach(s => {
            if (s.data && s.data.length > i) {
                row.push(s.data[i][1]);
            } else {
                row.push('');
            }
        });
        
        data.push(row);
    }
    
    // 根据格式导出
    if (format === 'csv') {
        const csvContent = [headers.join(','), ...data.map(row => row.join(','))].join('\n');
        downloadFile(csvContent, 'time_series_forecast.csv', 'text/csv');
    } else if (format === 'json') {
        const jsonData = data.map(row => {
            const obj = {};
            headers.forEach((header, index) => {
                obj[header] = row[index];
            });
            return obj;
        });
        downloadFile(JSON.stringify(jsonData, null, 2), 'time_series_forecast.json', 'application/json');
    }
}

// 下载文件辅助函数
function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
}

// 重置图表缩放
function resetChartZoom() {
    if (forecastChart) {
        forecastChart.dispatchAction({
            type: 'dataZoom',
            start: 0,
            end: 100
        });
    }
}

// 平滑滚动到预测区域
function scrollToForecast() {
    if (forecastChart) {
        const option = forecastChart.getOption();
        const series = option.series;
        
        // 找到预测数据系列
        const forecastSeries = series.find(s => s.name === '预测数据');
        if (forecastSeries && forecastSeries.data.length > 0) {
            // 计算预测开始的位置百分比
            const allData = series.reduce((acc, s) => {
                if (s.data) acc.push(...s.data);
                return acc;
            }, []);
            
            const forecastStartTime = forecastSeries.data[0][0];
            const totalTimeRange = Math.max(...allData.map(d => d[0])) - Math.min(...allData.map(d => d[0]));
            const forecastStartPercent = ((forecastStartTime - Math.min(...allData.map(d => d[0]))) / totalTimeRange) * 100;
            
            // 设置缩放到预测区域
            forecastChart.dispatchAction({
                type: 'dataZoom',
                start: Math.max(0, forecastStartPercent - 20),
                end: 100
            });
        }
    }
}


// Tooltip格式化函数
function tooltipFormatter(params) {
    // 获取时间戳并转换为日期对象
        const dateObj = new Date(params[0].value[0]);

        // 第一行：日期 (YYYY-MM-DD格式)
        const dateStr = dateObj.toLocaleDateString('zh-CN');

        // 第二行：采集时间 (HH:mm:ss格式)
        const timeStr = dateObj.toLocaleTimeString('zh-CN', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        // 第三行及后续：各系列的采集值
        let valueStr = '';
        params.forEach(param => {
            const value = param.value[1] !== null ? parseFloat(param.value[1]).toFixed(2) : 'N/A';
            valueStr += `<br/>${param.seriesName}: ${value}`;
        });

        // 组合三行数据
        return `${dateStr}<br/>${timeStr}${valueStr}`;
}