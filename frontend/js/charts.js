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
            formatter: function (params) {
                let result = params[0].axisValue + '<br/>';
                params.forEach(param => {
                    const color = param.color;
                    const seriesName = param.seriesName;
                    const value = typeof param.value === 'number' ? 
                        param.value.toFixed(2) : param.value[1].toFixed(2);
                    result += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>`;
                    result += `${seriesName}: ${value}<br/>`;
                });
                return result;
            }
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
function updateChart(data) {
    if (!forecastChart) {
        console.error('图表尚未初始化');
        return;
    }
    
    try {
        // 准备训练数据（历史数据）
        const historicalData = data.historical.dates.map((date, index) => [
            new Date(date).getTime(), 
            data.historical.values[index]
        ]);
        
        // 准备验证数据
        const validationData = data.validation && data.validation.dates ? 
            data.validation.dates.map((date, index) => [
                new Date(date).getTime(), 
                data.validation.values[index]
            ]) : [];
        
        // 准备验证预测数据
        const validationForecast = data.validation && data.validation.forecast ? 
            data.validation.dates.map((date, index) => [
                new Date(date).getTime(), 
                data.validation.forecast[index]
            ]) : [];
        
        // 准备预测数据
        const forecastData = data.forecast.dates.map((date, index) => [
            new Date(date).getTime(), 
            data.forecast.values[index]
        ]);
        
        // 计算Y轴范围
        const allValues = [
            ...data.historical.values,
            ...(data.validation ? data.validation.values : []),
            ...(data.validation && data.validation.forecast ? data.validation.forecast : []),
            ...data.forecast.values
        ];
        const minValue = Math.min(...allValues);
        const maxValue = Math.max(...allValues);
        const padding = (maxValue - minValue) * 0.1;
        
        // 更新图表配置
        const option = {
            title: {
                text: 'ARIMA存储空间使用率预测',
                subtext: `训练: ${data.historical.dates.length}, 验证: ${validationData.length}, 预测: ${data.forecast.dates.length} 个数据点`
            },
            yAxis: {
                min: Math.max(0, minValue - padding),
                max: maxValue + padding,
                name: '使用率 (%)'
            },
            series: [
                {
                    name: '训练数据',
                    data: historicalData
                },
                {
                    name: '验证数据',
                    data: validationData
                },
                {
                    name: '验证预测',
                    data: validationForecast
                },
                {
                    name: '预测数据',
                    data: forecastData
                }
            ]
        };
        
        // 如果没有验证数据，隐藏验证数据系列
        if (validationData.length === 0) {
            option.legend = {
                data: ['训练数据', '预测数据'],
                top: 40
            };
        }
        
        forecastChart.setOption(option, true);
        
        // 添加预测区域标记
        if (forecastData.length > 0) {
            const firstForecastTime = forecastData[0][0];
            forecastChart.setOption({
                graphic: [{
                    type: 'line',
                    shape: {
                        x1: 0, y1: 0, x2: 0, y2: 1
                    },
                    style: {
                        stroke: '#ff6b6b',
                        lineWidth: 2,
                        lineDash: [5, 5]
                    },
                    left: 'center',
                    top: 'middle'
                }]
            });
        }
        
        console.log('图表更新完成');
        
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