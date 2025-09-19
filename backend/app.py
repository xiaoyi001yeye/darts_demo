from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from darts import TimeSeries
from darts.models import ARIMA
from darts.metrics import mape, rmse, mae, mse
from darts.utils.statistics import check_seasonality, plot_acf, plot_pacf
import json
import numpy as np
from datetime import datetime, timedelta
import os
import warnings
import glob
import sys

# 设置系统编码为UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
    
warnings.filterwarnings('ignore')

app = Flask(__name__)
# 配置JSON编码，确保中文正常显示
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json;charset=utf-8'
CORS(app)  # 解决跨域问题

# 全局变量存储模型和数据
models_cache = {}
data_cache = {}
trained_model = None
train_series = None
val_series = None

def load_metric_data():
    """加载存储空间使用率数据"""
    # 查找data目录下的所有CSV文件
    # 支持多种路径：容器内部路径和本地开发路径
    data_dir = os.getenv('DATA_DIR', '/app/data')
    if not os.path.exists(data_dir):
        # 如果容器内路径不存在，尝试本地开发路径
        local_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        if os.path.exists(local_data_dir):
            data_dir = local_data_dir
        else:
            raise FileNotFoundError(f"数据目录不存在: {data_dir} 和 {local_data_dir}")
    
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    if not csv_files:
        raise FileNotFoundError(f"data目录中没有找到CSV文件: {data_dir}")
    
    # 读取所有CSV文件
    all_data = []
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            all_data.append(df)
        except Exception as e:
            print(f"警告: 无法读取文件 {file_path}: {e}")
    
    if not all_data:
        raise FileNotFoundError("没有成功读取任何CSV文件")
    
    # 合并所有数据
    df = pd.concat(all_data, ignore_index=True)
    
    # 转换时间列
    df['datetime'] = pd.to_datetime(df['time'])
    
    # 过滤有效数据 (value > 0，去除连接失败的数据)
    valid_data = df[df['value'] > 0].copy()
    
    if valid_data.empty:
        raise ValueError("没有找到有效的数据 (value > 0)")
    
    # 选择数据最完整的设备
    device_counts = valid_data['ci_id'].value_counts()
    best_device = device_counts.index[0]
    
    # 获取最佳设备的数据
    device_data = valid_data[valid_data['ci_id'] == best_device].copy()
    device_data = device_data.sort_values('datetime')
    
    # 按小时聚合数据（减少数据量，提高预测效果）
    device_data.set_index('datetime', inplace=True)
    hourly_data = device_data['value'].resample('H').mean().dropna()
    
    return hourly_data, best_device

def prepare_arima_data(series, train_ratio=0.8, 
                      data_start_date=None, data_end_date=None):
    """准备ARIMA模型的训练和验证数据，支持时间范围过滤"""
    # 转换为Darts TimeSeries
    ts = TimeSeries.from_series(series, freq='H')  # 小时频率
    
    # 根据指定的时间范围过滤数据
    if data_start_date or data_end_date:
        if data_start_date:
            ts = ts.drop_before(pd.Timestamp(data_start_date))
        if data_end_date:
            ts = ts.drop_after(pd.Timestamp(data_end_date))
    
    # 划分训练集和验证集
    train_size = int(len(ts) * train_ratio)
    ts_train = ts[:train_size]
    ts_val = ts[train_size:]
    
    return ts_train, ts_val

@app.route('/api/train', methods=['POST'])
def train_model():
    """训练ARIMA模型"""
    global trained_model, train_series, val_series
    
    try:
        # 获取参数
        data = request.json if request.json else {}
        p = int(data.get('p', 2))  # ARIMA的p参数
        d = int(data.get('d', 1))  # ARIMA的d参数
        q = int(data.get('q', 2))  # ARIMA的q参数
        train_ratio = float(data.get('train_ratio', 0.8))
        
        # 加载数据
        series_data, device_id = load_metric_data()
        
        # 准备训练数据
        train_series, val_series = prepare_arima_data(series_data, train_ratio)
        
        # 创建并训练ARIMA模型
        model = ARIMA(p=p, d=d, q=q)
        model.fit(train_series)
        trained_model = model
        
        # 在验证集上评估
        if len(val_series) > 0:
            val_forecast = model.predict(len(val_series))
            
            # 计算评估指标
            mape_score = float(mape(val_series, val_forecast))
            rmse_score = float(rmse(val_series, val_forecast))
            mae_score = float(mae(val_series, val_forecast))
            mse_score = float(mse(val_series, val_forecast))
        else:
            val_forecast = None
            mape_score = rmse_score = mae_score = mse_score = None
        
        # 准备响应数据
        response = {
            'success': True,
            'message': '模型训练完成',
            'model_params': {
                'p': p,
                'd': d, 
                'q': q,
                'model_type': 'ARIMA'
            },
            'data_info': {
                'device_id': device_id,
                'total_points': len(series_data),
                'train_points': len(train_series),
                'val_points': len(val_series),
                'data_frequency': 'hourly',
                'date_range': {
                    'start': series_data.index.min().strftime('%Y-%m-%d %H:%M:%S'),
                    'end': series_data.index.max().strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            'training_data': {
                'dates': train_series.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'values': train_series.values().flatten().tolist()
            },
            'validation_data': {
                'dates': val_series.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist() if len(val_series) > 0 else [],
                'values': val_series.values().flatten().tolist() if len(val_series) > 0 else [],
                'forecast': val_forecast.values().flatten().tolist() if val_forecast is not None else []
            },
            'metrics': {
                'mape': mape_score,
                'rmse': rmse_score,
                'mae': mae_score,
                'mse': mse_score
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'训练模型时出错: {str(e)}'}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """使用训练好的模型进行预测"""
    global trained_model, train_series
    
    try:
        if trained_model is None:
            return jsonify({'error': '请先训练模型'}), 400
        
        # 获取预测参数
        data = request.json if request.json else {}
        forecast_periods = int(data.get('periods', 24))  # 默认预测24小时
        
        # 进行预测
        forecast = trained_model.predict(forecast_periods)
        
        # 计算预测的置信区间（简单估计）
        forecast_values = forecast.values().flatten()
        
        # 基于训练数据的标准差估计置信区间
        train_std = np.std(train_series.values())
        confidence_lower = forecast_values - 1.96 * train_std
        confidence_upper = forecast_values + 1.96 * train_std
        
        # 准备响应数据
        response = {
            'success': True,
            'forecast': {
                'dates': forecast.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'values': forecast_values.tolist(),
                'confidence_lower': confidence_lower.tolist(),
                'confidence_upper': confidence_upper.tolist()
            },
            'forecast_info': {
                'periods': forecast_periods,
                'frequency': 'hourly',
                'model_type': 'ARIMA'
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'预测时出错: {str(e)}'}), 500

@app.route('/api/forecast', methods=['POST'])
def forecast():
    """完整的训练和预测流程（向后兼容）"""
    try:
        # 获取前端传递的参数
        data = request.json if request.json else {}
        forecast_periods = int(data.get('periods', 24))
        p = int(data.get('p', 2))
        d = int(data.get('d', 1)) 
        q = int(data.get('q', 2))
        train_ratio = float(data.get('train_ratio', 0.8))
        trend = data.get('trend', 'c')
        seasonal_order_P = int(data.get('seasonal_order_P', 0))
        seasonal_order_D = int(data.get('seasonal_order_D', 0))
        seasonal_order_Q = int(data.get('seasonal_order_Q', 0))
        seasonal_periods = int(data.get('seasonal_periods', 24))
        
        # 获取时间范围参数
        data_start_date = data.get('data_start_date')
        data_end_date = data.get('data_end_date')

        # 构建季节性参数
        seasonal_order = (seasonal_order_P, seasonal_order_D, seasonal_order_Q, seasonal_periods)

        # 加载数据
        series_data, device_id = load_metric_data()

        # 准备训练数据
        train_series, val_series = prepare_arima_data(
            series_data, 
            train_ratio=train_ratio,
            data_start_date=data_start_date,
            data_end_date=data_end_date
        )

        # 创建并训练ARIMA模型
        # 注意：Darts的ARIMA实现与statsmodels略有不同，需要调整参数
        model = ARIMA(p=p, d=d, q=q, trend=trend)
        model.fit(train_series)

        # 预测
        forecast = model.predict(forecast_periods)

        # 在验证集上评估（如果有足够的验证数据）
        if len(val_series) >= forecast_periods:
            val_forecast = model.predict(len(val_series))
            actual = val_series

            mape_score = float(mape(actual, val_forecast))
            rmse_score = float(rmse(actual, val_forecast))
            mae_score = float(mae(actual, val_forecast))
            mse_score = float(mse(actual, val_forecast))
        else:
            val_forecast = None
            mape_score = rmse_score = mae_score = mse_score = None

        # 准备响应数据
        response = {
            'historical': {
                'dates': train_series.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'values': train_series.values().flatten().tolist()
            },
            'forecast': {
                'dates': forecast.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'values': forecast.values().flatten().tolist()
            },
            'validation': {
                'dates': val_series.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist() if len(val_series) > 0 else [],
                'values': val_series.values().flatten().tolist() if len(val_series) > 0 else [],
                'forecast': val_forecast.values().flatten().tolist() if val_forecast is not None else []
            },
            'metrics': {
                'mape': mape_score,
                'rmse': rmse_score,
                'mae': mae_score,
                'mse': mse_score
            },
            'model_info': {
                'type': 'ARIMA',
                'parameters': f'ARIMA({p},{d},{q}) with trend={trend}',
                'device_id': device_id,
                'train_size': len(train_series),
                'val_size': len(val_series),
                'forecast_periods': forecast_periods,
                'data_frequency': 'hourly'
            }
        }
        
        return jsonify(json.dumps(response))
    
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    models = [
        {
            'id': 'arima', 
            'name': 'ARIMA (自回归积分滑动平均)', 
            'description': '专用于存储空间使用率预测的ARIMA模型',
            'parameters': {
                'p': {'default': 2, 'min': 0, 'max': 5, 'description': '自回归阶数'},
                'd': {'default': 1, 'min': 0, 'max': 2, 'description': '差分阶数'},
                'q': {'default': 2, 'min': 0, 'max': 5, 'description': '移动平均阶数'}
            }
        }
    ]
    return jsonify(models)

# 添加获取模型参数配置的接口
@app.route('/api/model/<model_id>/parameters', methods=['GET'])
def get_model_parameters(model_id):
    """获取指定模型的参数配置"""
    # 定义各模型的参数配置
    model_parameters = {
        'arima': {
            'p': {'type': 'number', 'default': 2, 'min': 0, 'max': 5, 'description': '自回归阶数'},
            'd': {'type': 'number', 'default': 1, 'min': 0, 'max': 2, 'description': '差分阶数'},
            'q': {'type': 'number', 'default': 2, 'min': 0, 'max': 5, 'description': '移动平均阶数'},
            'train_ratio': {'type': 'number', 'default': 0.8, 'min': 0.5, 'max': 0.95, 'step': 0.05, 'description': '训练集比例'},
            'trend': {'type': 'select', 'options': ['n', 'c', 't', 'ct'], 'default': 'c', 'description': '趋势参数'},
            'seasonal_order_P': {'type': 'number', 'default': 0, 'min': 0, 'max': 3, 'description': '季节性自回归阶数'},
            'seasonal_order_D': {'type': 'number', 'default': 0, 'min': 0, 'max': 2, 'description': '季节性差分阶数'},
            'seasonal_order_Q': {'type': 'number', 'default': 0, 'min': 0, 'max': 3, 'description': '季节性移动平均阶数'},
            'seasonal_periods': {'type': 'number', 'default': 24, 'min': 1, 'max': 168, 'description': '季节性周期(小时)'}
        }
    }
    
    if model_id in model_parameters:
        return jsonify({
            'model_id': model_id,
            'parameters': model_parameters[model_id]
        })
    else:
        return jsonify({'error': '模型未找到'}), 404

@app.route('/api/data/info', methods=['GET'])
def get_data_info():
    """获取数据信息"""
    try:
        series_data, device_id = load_metric_data()
        
        response = {
            'device_id': device_id,
            'total_points': len(series_data),
            'date_range': {
                'start': series_data.index.min().strftime('%Y-%m-%d %H:%M:%S'),
                'end': series_data.index.max().strftime('%Y-%m-%d %H:%M:%S')
            },
            'frequency': 'hourly',
            'statistics': {
                'mean': float(series_data.mean()),
                'std': float(series_data.std()),
                'min': float(series_data.min()),
                'max': float(series_data.max()),
                'median': float(series_data.median())
            }
        }
        
        return jsonify({
            "status": "success",
            "data": response
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/data/preview', methods=['GET'])
def preview_data():
    """预览数据"""
    try:
        # 调用load_metric_data函数加载存储空间使用率数据，并获取时间序列数据和设备ID
        series_data, device_id = load_metric_data()
        
        # 从时间序列数据中提取最近的100个数据点用于预览
        preview_data = series_data.tail(100)
        
        # 初始化一个空列表，用于存储预览数据记录
        records = []
        # 遍历预览数据中的每个数据点
        for i in range(len(preview_data)):
            # 将每个数据点转换为字典格式并添加到记录列表中
            records.append({
                # 将时间戳转换为字符串格式 'YYYY-MM-DD HH:MM:SS'
                'time': preview_data.index[i].strftime('%Y-%m-%d %H:%M:%S'),
                # 添加设备ID
                'ci_id': device_id,
                # 将数值转换为浮点数格式
                'value': float(preview_data.iloc[i])
            })
        
        # 构建响应数据结构
        response = {
            # 添加设备ID
            'device_id': device_id,
            # 添加数据记录列表
            'data': records,
            # 添加总数据点数
            'total_points': len(series_data),
            # 添加预览数据点数
            'preview_points': len(preview_data),
            # 添加数据时间范围信息
            'date_range': {
                # 添加数据起始时间
                'start': series_data.index.min().strftime('%Y-%m-%d %H:%M:%S'),
                # 添加数据结束时间
                'end': series_data.index.max().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        # 返回成功的JSON响应，包含状态和预览数据
        return jsonify({
            "status": "success",
            "data": response
        })
    
    # 捕获可能出现的异常
    except Exception as e:
        # 返回错误的JSON响应，包含状态和错误信息
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/data/preview2', methods=['GET'])
def preview_data2():
    """预览数据 - 按设备统计数据概况"""
    try:
        # 查找data目录下的所有CSV文件
        data_dir = os.getenv('DATA_DIR', '/app/data')
        if not os.path.exists(data_dir):
            # 如果容器内路径不存在，尝试本地开发路径
            local_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
            if os.path.exists(local_data_dir):
                data_dir = local_data_dir
            else:
                raise FileNotFoundError(f"数据目录不存在: {data_dir} 和 {local_data_dir}")

        csv_files = glob.glob(os.path.join(data_dir, '*.csv'))

        if not csv_files:
            raise FileNotFoundError(f"data目录中没有找到CSV文件: {data_dir}")

        # 读取所有CSV文件
        all_data = []
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                all_data.append(df)
            except Exception as e:
                print(f"警告: 无法读取文件 {file_path}: {e}")

        if not all_data:
            raise FileNotFoundError("没有成功读取任何CSV文件")

        # 合并所有数据
        df = pd.concat(all_data, ignore_index=True)

        # 转换时间列
        df['datetime'] = pd.to_datetime(df['time'])

        # 按设备分组进行统计
        device_stats = []

        # 对每个设备进行分组统计
        for ci_id, group in df.groupby('ci_id'):
            # 获取设备类型（取第一个非空值）
            ci_type = group['ci_type'].iloc[0] if not group['ci_type'].empty else 'unknown'

            # 获取数据代码（取第一个非空值）
            code = group['code'].iloc[0] if not group['code'].empty else 'unknown'

            # 计算时间范围
            data_start_time = group['datetime'].min().strftime('%Y-%m-%d %H:%M:%S')
            data_end_time = group['datetime'].max().strftime('%Y-%m-%d %H:%M:%S')

            # 统计正常值和异常值
            normal_count = len(group[group['value'] != -2])
            abnormal_count = len(group[group['value'] == -2])

            # 构建设备统计信息
            device_stat = {
                'ci_id': ci_id,
                'ci_type': ci_type,
                'data_start_time': data_start_time,
                'data_end_time': data_end_time,
                'code': code,
                'normal_count': normal_count,
                'abnormal_count': abnormal_count
            }

            device_stats.append(device_stat)

        # 按正常数据量降序排序（数据质量好的设备排在前面）
        device_stats.sort(key=lambda x: x['normal_count'], reverse=True)

        # 计算总体统计信息
        total_records = len(df)
        total_devices = len(device_stats)
        total_normal = sum(stat['normal_count'] for stat in device_stats)
        total_abnormal = sum(stat['abnormal_count'] for stat in device_stats)

        # 构建响应数据结构
        response = {
            'summary': {
                'total_devices': total_devices,
                'total_records': total_records,
                'total_normal_count': total_normal,
                'total_abnormal_count': total_abnormal,
                'data_quality_ratio': round(total_normal / total_records * 100, 2) if total_records > 0 else 0
            },
            'records': device_stats,
            'data_range': {
                'start': df['datetime'].min().strftime('%Y-%m-%d %H:%M:%S'),
                'end': df['datetime'].max().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        # 返回成功的JSON响应，包含状态和预览数据
        return jsonify({
            "status": "success",
            "data": response
        })

    # 捕获可能出现的异常
    except Exception as e:
        # 返回错误的JSON响应，包含状态和错误信息
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    print("启动存储空间使用率预测系统后端...")
    print("后端服务地址: http://localhost:5001")
    print("API文档:")
    print("  GET  /api/health        - 健康检查")
    print("  GET  /api/models        - 获取可用模型")
    print("  POST /api/train         - 训练ARIMA模型")
    print("  POST /api/predict       - 使用训练好的模型预测")
    print("  POST /api/forecast      - 完整的训练和预测流程")
    print("  GET  /api/data/info     - 获取数据信息")
    print("  GET  /api/data/preview  - 预览数据")
    print("\n数据文件: data/tb_metric_raw_free_space_ratio_202509161435.csv")
    print("专门用于存储空间使用率的ARIMA时间序列预测")
    
    app.run(debug=True, port=5001, host='0.0.0.0')