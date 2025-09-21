from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from darts import TimeSeries
from darts.metrics import mape, rmse, mae, mse
import json
import numpy as np
from datetime import datetime, timedelta
import os
import warnings
import glob
import sys
# 添加模型管理器导入
from models.model_manager import ModelManager

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

# 创建全局模型管理器实例
model_manager = ModelManager()

def load_metric_data(resource_id=None):
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
    
    # 如果指定了资源ID，则过滤数据
    if resource_id:
        df = df[df['ci_id'] == resource_id]
    
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
     # 1. 首先处理无效值 (-2 表示连接失败)
    series = series[series > 0]  # 过滤掉无效值

    # 2. 重新索引到规则的5分钟频率时间序列，填充缺失值
    series = series.asfreq('5T')  # '5T' 表示5分钟频率

    # 3. 处理缺失值 - 可以选择插值或前向填充
    series = series.interpolate(method='time')  # 时间序列插值
    # 或者使用前向填充: series = series.fillna(method='ffill')
    # 转换为Darts TimeSeries
    # ts = TimeSeries.from_series(series, freq='H')  # 小时频率
    # 如果原始数据是分钟级
    # ts = TimeSeries.from_series(series, freq='T')  # 分钟频率
    # 如果原始数据是秒级
    # ts = TimeSeries.from_series(series, freq='S')  # 秒频率
    ts = TimeSeries.from_series(series, freq='5T')
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



@app.route('/api/forecast', methods=['POST'])
def forecast():
    """完整的训练和预测流程（向后兼容）"""
    try:
        # 获取前端传递的参数
        data = request.json if request.json else {}
        model_type = data.get('model', 'arima')
        forecast_periods = int(data.get('periods', 24))
        train_ratio = float(data.get('train_ratio', 0.8))

        # 获取时间范围参数
        data_start_date = data.get('data_start_date')
        data_end_date = data.get('data_end_date')
        
        # 获取资源ID参数
        resource_id = data.get('resource_id')

        # 加载数据，支持根据资源ID过滤
        series_data, device_id = load_metric_data(resource_id)

        # 准备训练数据
        train_series, val_series = prepare_arima_data(
            series_data, 
            train_ratio=train_ratio,
            data_start_date=data_start_date,
            data_end_date=data_end_date
        )

        # 根据模型类型创建模型
        model_obj = model_manager.get_model(model_type)
        if not model_obj:
            return jsonify({'error': f'不支持的模型类型: {model_type}'}), 400
            
        # 创建并训练模型
        model = model_obj.create_model(**data)
        model = model_obj.fit(model, train_series)
        
        # 获取模型参数描述
        model_params = str(data)  # 简化处理，实际应根据模型类型生成具体描述

        # 预测
        forecast = model_obj.predict(model, forecast_periods)

        # 在验证集上评估（如果有足够的验证数据）
        if len(val_series) >= forecast_periods:
            val_forecast = model_obj.predict(model, len(val_series))
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
                'type': model_type,
                'parameters': model_params,
                'device_id': device_id,
                'train_size': len(train_series),
                'val_size': len(val_series),
                'forecast_periods': forecast_periods,
                'data_frequency': 'hourly'
            }
        }
        
        return json.dumps(response)
    
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    models = model_manager.get_available_models()
    return jsonify(models)

# 添加获取模型参数配置的接口
@app.route('/api/model/<model_id>/parameters', methods=['GET'])
def get_model_parameters(model_id):
    """获取指定模型的参数配置"""
    parameters = model_manager.get_model_parameters(model_id)
    
    if parameters:
        return jsonify({
            'model_id': model_id,
            'parameters': parameters
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
    print("  POST /api/forecast      - 完整的训练和预测流程")
    print("  GET  /api/data/info     - 获取数据信息")
    print("  GET  /api/data/preview  - 预览数据")
    print("\n数据文件: data/tb_metric_raw_free_space_ratio_202509161435.csv")
    print("专门用于存储空间使用率的ARIMA时间序列预测")
    
    app.run(debug=True, port=5001, host='0.0.0.0')