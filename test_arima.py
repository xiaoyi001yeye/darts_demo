#!/usr/bin/env python3
"""
测试ARIMA模型的训练和预测功能
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from darts import TimeSeries
from darts.models import ARIMA
from darts.metrics import mape, rmse, mae, mse
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

def load_metric_data():
    """加载存储空间使用率数据"""
    data_file = 'data/tb_metric_raw_free_space_ratio_202509161435.csv'
    
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"数据文件不存在: {data_file}")
    
    # 读取数据
    df = pd.read_csv(data_file)
    
    # 转换时间列
    df['datetime'] = pd.to_datetime(df['time'])
    
    # 过滤有效数据 (value > 0，去除连接失败的数据)
    valid_data = df[df['value'] > 0].copy()
    
    # 选择数据最完整的设备
    device_counts = valid_data['ci_id'].value_counts()
    best_device = device_counts.index[0]
    
    print(f"选择设备: {best_device}")
    print(f"设备数据量: {device_counts[best_device]}")
    
    # 获取最佳设备的数据
    device_data = valid_data[valid_data['ci_id'] == best_device].copy()
    device_data = device_data.sort_values('datetime')
    
    # 按小时聚合数据（减少数据量，提高预测效果）
    device_data.set_index('datetime', inplace=True)
    hourly_data = device_data['value'].resample('H').mean().dropna()
    
    return hourly_data, best_device

def prepare_arima_data(series, train_ratio=0.8):
    """准备ARIMA模型的训练和验证数据"""
    # 转换为Darts TimeSeries
    ts = TimeSeries.from_series(series)
    
    # 划分训练集和验证集
    train_size = int(len(ts) * train_ratio)
    train_series = ts[:train_size]
    val_series = ts[train_size:]
    
    return train_series, val_series

def train_arima_model(train_series, p=2, d=1, q=2):
    """训练ARIMA模型"""
    print(f"训练ARIMA({p},{d},{q})模型...")
    model = ARIMA(p=p, d=d, q=q)
    model.fit(train_series)
    print("模型训练完成!")
    return model

def evaluate_model(model, val_series):
    """评估模型性能"""
    if len(val_series) == 0:
        return None
    
    val_forecast = model.predict(len(val_series))
    
    # 计算评估指标
    mape_score = float(mape(val_series, val_forecast))
    rmse_score = float(rmse(val_series, val_forecast))
    mae_score = float(mae(val_series, val_forecast))
    mse_score = float(mse(val_series, val_forecast))
    
    metrics = {
        'mape': mape_score,
        'rmse': rmse_score,
        'mae': mae_score,
        'mse': mse_score
    }
    
    print("\n=== 模型评估指标 ===")
    print(f"MAPE: {mape_score:.2f}%")
    print(f"RMSE: {rmse_score:.2f}")
    print(f"MAE: {mae_score:.2f}")
    print(f"MSE: {mse_score:.2f}")
    
    return metrics, val_forecast

def predict_future(model, periods=24):
    """预测未来数据"""
    print(f"\n预测未来{periods}小时的存储空间使用率...")
    forecast = model.predict(periods)
    
    # 计算简单的置信区间
    forecast_values = forecast.values().flatten()
    print(f"预测值范围: {forecast_values.min():.2f}% - {forecast_values.max():.2f}%")
    print(f"预测平均值: {forecast_values.mean():.2f}%")
    
    return forecast

def plot_results(train_series, val_series, val_forecast=None, future_forecast=None):
    """绘制结果图表"""
    plt.figure(figsize=(15, 8))
    
    # 训练数据
    plt.plot(train_series.time_index, train_series.values(), 
             label='训练数据', color='blue', linewidth=2)
    
    # 验证数据
    if len(val_series) > 0:
        plt.plot(val_series.time_index, val_series.values(), 
                 label='验证数据', color='green', linewidth=2)
        
        # 验证预测
        if val_forecast is not None:
            plt.plot(val_series.time_index, val_forecast.values(), 
                     label='验证预测', color='green', linestyle='--', linewidth=2)
    
    # 未来预测
    if future_forecast is not None:
        plt.plot(future_forecast.time_index, future_forecast.values(), 
                 label='未来预测', color='red', linestyle='--', linewidth=3)
    
    plt.title('ARIMA存储空间使用率预测', fontsize=16, fontweight='bold')
    plt.xlabel('时间', fontsize=12)
    plt.ylabel('使用率 (%)', fontsize=12)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图片
    plt.savefig('arima_forecast_result.png', dpi=300, bbox_inches='tight')
    print("\n图表已保存为: arima_forecast_result.png")
    plt.show()

def main():
    """主函数"""
    print("=== ARIMA存储空间使用率预测测试 ===\n")
    
    try:
        # 1. 加载数据
        print("1. 加载数据...")
        series_data, device_id = load_metric_data()
        print(f"数据时间范围: {series_data.index.min()} 到 {series_data.index.max()}")
        print(f"数据点数: {len(series_data)}")
        print(f"数据统计: 平均{series_data.mean():.2f}%, 最小{series_data.min():.2f}%, 最大{series_data.max():.2f}%")
        
        # 2. 准备训练数据
        print("\n2. 准备训练数据...")
        train_series, val_series = prepare_arima_data(series_data, train_ratio=0.8)
        print(f"训练数据: {len(train_series)} 个点")
        print(f"验证数据: {len(val_series)} 个点")
        
        # 3. 训练模型
        print("\n3. 训练ARIMA模型...")
        model = train_arima_model(train_series, p=2, d=1, q=2)
        
        # 4. 评估模型
        print("\n4. 评估模型性能...")
        metrics, val_forecast = evaluate_model(model, val_series)
        
        # 5. 预测未来
        print("\n5. 预测未来24小时...")
        future_forecast = predict_future(model, periods=24)
        
        # 6. 可视化结果
        print("\n6. 绘制结果图表...")
        plot_results(train_series, val_series, val_forecast, future_forecast)
        
        print("\n=== 测试完成 ===")
        print("模型已成功训练并生成预测结果!")
        
        return {
            'device_id': device_id,
            'model': model,
            'metrics': metrics,
            'train_data': train_series,
            'val_data': val_series,
            'val_forecast': val_forecast,
            'future_forecast': future_forecast
        }
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = main()