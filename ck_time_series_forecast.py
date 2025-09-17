import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from clickhouse_driver import Client
from darts import TimeSeries
from darts.models import Prophet, ARIMA, ExponentialSmoothing, XGBModel, LightGBMModel, CatBoostModel, LinearRegressionModel, RandomForest
from darts.metrics import mape, rmse, mae
from sklearn.ensemble import VotingRegressor
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.family'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 连接到ClickHouse
def connect_clickhouse(host='localhost', port=9000, user='default', password='', database='default'):
    """连接到ClickHouse数据库"""
    try:
        client = Client(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=10,
            send_receive_timeout=30
        )
        # 测试连接
        result = client.execute('SELECT 1')
        print(f"成功连接到ClickHouse: {host}:{port}")
        return client
    except Exception as e:
        print(f"连接ClickHouse失败: {e}")
        print(f"尝试连接的地址: {host}:{port}")
        print("请检查:")
        print("1. 端口是否正确 (通常为 9000)")
        print("2. 网络连接是否正常")
        print("3. ClickHouse 服务是否运行")
        print("4. 防火墙设置")
        return None

# 从ClickHouse读取数据
def fetch_data_from_clickhouse(client, target_date, table_name):
    """
    从ClickHouse读取指定日期的指标数据
    数据应包含time和value字段，每5分钟一个数据点
    """
    if not client:
        return None
    
    # 构建查询日期范围 (一整天)
    start_date = f"{target_date} 00:00:00"
    end_date = f"{target_date} 23:59:59"
    
    # 查询语句 - 请根据实际表结构和字段名调整
    query = f"""
    select time,value from tb_metric_raw where code ='tps' and ci_id ='000000000020571d' order by time asc; 
    """
    
    try:
        # 执行查询
        result = client.execute(query)
        
        # 转换为DataFrame
        df = pd.DataFrame(result, columns=['time', 'value'])
        df['time'] = pd.to_datetime(df['time'])
        
        print(f"成功读取数据: {len(df)} 条记录")
        print(f"时间范围: {df['time'].min()} 至 {df['time'].max()}")
        
        return df
    except Exception as e:
        print(f"读取数据失败: {e}")
        return None

# 准备时间序列数据
def prepare_time_series(df):
    """将DataFrame转换为Darts的TimeSeries对象"""
    # 确保数据按时间排序
    df = df.sort_values('time')
    
    # 创建TimeSeries对象
    series = TimeSeries.from_dataframe(
        df,
        time_col='time',
        value_cols='value',
        freq='5T'  # 5分钟频率
    )
    
    return series

# 拆分训练集和验证集
def split_train_validation(series, train_ratio=0.8):
    """将时间序列拆分为训练集和验证集"""
    train_size = int(len(series) * train_ratio)
    train, val = series[:train_size], series[train_size:]
    
    print(f"训练集大小: {len(train)} 个数据点")
    print(f"验证集大小: {len(val)} 个数据点")
    
    return train, val

# 训练模型并进行预测
def train_and_forecast(train, val):
    """训练多个模型并在验证集上进行预测"""
    # 初始化模型
    models = {
        # 统计学习模型
        "Prophet": Prophet(daily_seasonality=True, weekly_seasonality=False, yearly_seasonality=False),
        "ARIMA": ARIMA(p=2, d=1, q=2),
        "Exponential Smoothing": ExponentialSmoothing(seasonal_periods=24),
        
        # 机器学习模型
        "XGBoost": XGBModel(
            lags=24, # 设置滞后项，可以是一个整数或列表
            output_chunk_length=1,
            random_state=42
        ),
        "LightGBM": LightGBMModel(
            lags=24,
            output_chunk_length=1,
            random_state=42,
            verbose=-1
        ),
        "CatBoost": CatBoostModel(
            lags=4,
            output_chunk_length=1,
            random_state=42,
            verbose=False
        ),
        "Random Forest": RandomForest(
            lags=24,
            output_chunk_length=1,
            random_state=42,
            n_estimators=100
        ),
        "Linear Regression": LinearRegressionModel(
            lags=24,
            output_chunk_length=1
        )
    }
    
    results = {}
    forecasts = {}
    
    # 训练每个模型并进行预测
    for name, model in models.items():
        print(f"\n训练 {name} 模型...")
        
        try:
            # 训练模型
            model.fit(train)
            
            # 进行预测
            forecast = model.predict(len(val))
            
            # 计算评估指标
            model_mape = mape(val, forecast)
            model_rmse = rmse(val, forecast)
            model_mae = mae(val, forecast)
            
            print(f"{name} 模型评估:")
            print(f"  MAPE: {model_mape:.2f}%")
            print(f"  RMSE: {model_rmse:.2f}")
            print(f"  MAE: {model_mae:.2f}")
            
            results[name] = {
                "model": model,
                "forecast": forecast,
                "mape": model_mape,
                "rmse": model_rmse,
                "mae": model_mae
            }
            
            forecasts[name] = forecast
            
        except Exception as e:
            print(f"{name} 模型训练失败: {e}")
            continue
    
    return results, forecasts

# 实现集成学习
def ensemble_forecast(forecasts, val, method='average'):
    """
    集成多个模型的预测结果
    method: 'average', 'weighted_average', 'median'
    """
    if not forecasts:
        return None
    
    # 过滤掉空的预测结果
    valid_forecasts = {name: fcst for name, fcst in forecasts.items() if fcst is not None}
    
    if not valid_forecasts:
        return None, None, None, None
        
    forecast_values = []
    model_names = []
    
    for name, forecast in valid_forecasts.items():
        # 确保所有预测结果的长度相同
        if len(forecast) == len(val):
            forecast_values.append(forecast.values().flatten())
            model_names.append(name)
        else:
            print(f"警告: 模型 {name} 的预测长度与验证集不匹配，跳过集成")
            
    if not forecast_values:
        return None, None, None, None
        
    forecast_array = np.array(forecast_values)
    
    if method == 'average':
        # 简单平均
        ensemble_values = np.mean(forecast_array, axis=0)
    elif method == 'weighted_average':
        # 基于MAPE的加权平均（MAPE越小权重越大）
        weights = []
        for name in model_names:
            if name in valid_forecasts:
                # 计算权重（MAPE的倒数）
                model_mape = mape(val, valid_forecasts[name])
                weight = 1.0 / (model_mape + 1e-6)  # 避免除零
                weights.append(weight)
        
        weights = np.array(weights)
        weights = weights / np.sum(weights)  # 归一化权重
        
        print("模型权重:")
        for i, name in enumerate(model_names):
            print(f"  {name}: {weights[i]:.3f}")
        
        ensemble_values = np.average(forecast_array, axis=0, weights=weights)
    elif method == 'median':
        # 中位数集成
        ensemble_values = np.median(forecast_array, axis=0)
    else:
        raise ValueError(f"不支持的集成方法: {method}")
    
    # 创建TimeSeries对象
    ensemble_forecast = TimeSeries.from_values(
        ensemble_values,
        start=val.start_time(),
        freq=val.freq
    )
    
    # 计算集成模型的评估指标
    ensemble_mape = mape(val, ensemble_forecast)
    ensemble_rmse = rmse(val, ensemble_forecast)
    ensemble_mae = mae(val, ensemble_forecast)
    
    print(f"\n集成模型 ({method}) 评估:")
    print(f"  MAPE: {ensemble_mape:.2f}%")
    print(f"  RMSE: {ensemble_rmse:.2f}")
    print(f"  MAE: {ensemble_mae:.2f}")
    
    return ensemble_forecast, ensemble_mape, ensemble_rmse, ensemble_mae

# 可视化结果
def plot_results(train, val, results, ensemble_results=None):
    """可视化训练数据、验证数据和预测结果"""
    plt.figure(figsize=(18, 12))
    
    # 创建子图
    plt.subplot(2, 1, 1)
    
    # 绘制训练数据和验证数据
    train.plot(label='训练数据', color='blue', alpha=0.7)
    val.plot(label='验证数据', color='green', alpha=0.8, linewidth=2)
    
    # 绘制每个模型的预测结果
    colors = ['red', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
    color_index = 0
    
    for name, result in results.items():
        if result['forecast'] is not None:
            result['forecast'].plot(label=f'{name} (MAPE: {result["mape"]:.1f}%)', 
                                  color=colors[color_index % len(colors)], alpha=0.7)
            color_index += 1
    
    # 绘制集成预测结果
    if ensemble_results:
        for method, (forecast, mape_score, _, _) in ensemble_results.items():
            if forecast is not None:
                forecast.plot(label=f'集成-{method} (MAPE: {mape_score:.1f}%)', 
                             color='black', linewidth=3, linestyle='--')
    
    plt.title('时间序列预测结果对比', fontsize=14)
    plt.xlabel('时间')
    plt.ylabel('指标值')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # 第二个子图：误差分析
    # plt.subplot(2, 1, 2)
    
    # model_names = []
    # mape_scores = []
    
    # for name, result in results.items():
    #     if result['forecast'] is not None:
    #         model_names.append(name)
    #         mape_scores.append(result['mape'])
    
    # if ensemble_results:
    #     for method, (_, mape_score, _, _) in ensemble_results.items():
    #         if mape_score is not None:
    #             model_names.append(f'集成-{method}')
    #             mape_scores.append(mape_score)
    
    # bars = plt.bar(range(len(model_names)), mape_scores, alpha=0.7)
    # plt.xlabel('模型')
    # plt.ylabel('MAPE (%)')
    # plt.title('模型性能对比 (MAPE)', fontsize=14)
    # plt.xticks(range(len(model_names)), model_names, rotation=45, ha='right')
    # plt.grid(True, alpha=0.3)
    
    # # 在柱状图上显示数值
    # for i, bar in enumerate(bars):
    #     height = bar.get_height()
    #     plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
    #             f'{height:.1f}%', ha='center', va='bottom')
    
    # plt.tight_layout()
    plt.show()

# 模型排名和分析
def analyze_model_performance(results, ensemble_results=None):
    """分析模型性能并给出排名"""
    print("\n" + "="*50)
    print("模型性能分析报告")
    print("="*50)
    
    # 收集所有模型的结果
    all_results = {}
    
    for name, result in results.items():
        if result['forecast'] is not None:
            all_results[name] = {
                'mape': result['mape'],
                'rmse': result['rmse'],
                'mae': result['mae']
            }
    
    if ensemble_results:
        for method, (_, mape_score, rmse_score, mae_score) in ensemble_results.items():
            if mape_score is not None:
                all_results[f'集成-{method}'] = {
                    'mape': mape_score,
                    'rmse': rmse_score,
                    'mae': mae_score
                }
    
    if not all_results:
        print("没有可用于分析的模型结果。")
        return

    # 按MAPE排序
    sorted_results = sorted(all_results.items(), key=lambda x: x[1]['mape'])
    
    print("\n模型排名 (按MAPE从小到大):")
    print("-" * 60)
    print(f"{'排名':<4} {'模型名称':<20} {'MAPE':<10} {'RMSE':<10} {'MAE':<10}")
    print("-" * 60)
    
    for i, (name, metrics) in enumerate(sorted_results, 1):
        print(f"{i:<4} {name:<20} {metrics['mape']:<10.2f} {metrics['rmse']:<10.2f} {metrics['mae']:<10.2f}")
    
    # 分析最佳模型
    best_model = sorted_results[0]
    print(f"\n🏆 最佳模型: {best_model[0]}")
    print(f"   MAPE: {best_model[1]['mape']:.2f}%")
    print(f"   RMSE: {best_model[1]['rmse']:.2f}")
    print(f"   MAE: {best_model[1]['mae']:.2f}")

# 主函数
def main():
    # ClickHouse连接参数 - 请根据实际情况修改
    clickhouse_params = {
        'host': '172.17.162.210',
        'port': 30156,
        'user': 'default',
        'password': 'Yh45EWxZnww9JX',
        'database': 'default'
    }
    
    # 目标日期和表名 - 请根据实际情况修改
    target_date = '2025-09-13'  # 要分析的日期
    table_name = 'metrics_table'  # 存储指标数据的表名
    
    # 连接到ClickHouse
    client = connect_clickhouse(**clickhouse_params)
    if not client:
        return
    
    # 读取数据
    df = fetch_data_from_clickhouse(client, target_date, table_name)
    if df is None or len(df) == 0:
        print("没有获取到数据，程序退出")
        return
    
    # 准备时间序列
    series = prepare_time_series(df)
    
    # 拆分训练集和验证集
    train, val = split_train_validation(series)
    
    # 训练模型并预测
    print("开始训练多个预测模型...")
    results, forecasts = train_and_forecast(train, val)
    
    if not results:
        print("没有成功训练任何模型")
        return
    
    # 实现集成学习
    print("\n开始集成学习...")
    ensemble_results = {}
    
    # 尝试不同的集成方法
    for method in ['average', 'weighted_average', 'median']:
        try:
            ensemble_forecast_result, mape_score, rmse_score, mae_score = ensemble_forecast(
                forecasts, val, method=method
            )
            ensemble_results[method] = (ensemble_forecast_result, mape_score, rmse_score, mae_score)
        except Exception as e:
            print(f"集成方法 {method} 失败: {e}")
    
    # 可视化结果
    plot_results(train, val, results, ensemble_results)
    
    # 分析模型性能
    analyze_model_performance(results, ensemble_results)

if __name__ == "__main__":
    main()