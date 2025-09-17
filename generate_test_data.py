#!/usr/bin/env python3
"""
生成测试数据的脚本
创建模拟的存储空间使用率数据，用于测试接口
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_test_data():
    """生成模拟的存储空间使用率数据"""
    # 设置参数
    start_date = datetime.now() - timedelta(days=30)  # 30天的数据
    end_date = datetime.now()
    
    # 生成时间序列（每小时一个数据点）
    time_range = pd.date_range(start=start_date, end=end_date, freq='H')
    
    # 生成模拟的存储空间使用率数据
    np.random.seed(42)  # 确保可重复性
    
    data_points = []
    base_usage = 65.0  # 基础使用率65%
    
    for i, timestamp in enumerate(time_range):
        # 添加趋势（缓慢增长）
        trend = i * 0.01
        
        # 添加季节性（每天的周期）
        seasonal = 5 * np.sin(2 * np.pi * i / 24)
        
        # 添加随机噪声
        noise = np.random.normal(0, 2)
        
        # 计算最终值
        value = base_usage + trend + seasonal + noise
        
        # 确保值在合理范围内 (30% - 95%)
        value = max(30.0, min(95.0, value))
        
        data_points.append({
            'time': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'ci_id': 'test_device_001',
            'value': round(value, 2)
        })
    
    # 创建DataFrame
    df = pd.DataFrame(data_points)
    
    # 保存到测试数据目录
    test_data_path = '/Users/weiyi/code/darts_demo/test_data/tb_metric_raw_free_space_ratio_202509161435.csv'
    df.to_csv(test_data_path, index=False)
    
    print(f"测试数据已生成: {test_data_path}")
    print(f"数据点数量: {len(df)}")
    print(f"数据范围: {df['value'].min():.2f}% - {df['value'].max():.2f}%")
    print(f"时间范围: {df['time'].min()} - {df['time'].max()}")
    
    return test_data_path

if __name__ == '__main__':
    generate_test_data()