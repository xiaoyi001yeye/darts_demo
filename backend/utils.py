import pandas as pd
import numpy as np
from darts import TimeSeries
from darts.dataprocessing.transformers import Scaler, MissingValuesFiller
from darts.metrics import mape, rmse, mae, mse
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimeSeriesPreprocessor:
    """时间序列数据预处理类"""
    
    def __init__(self):
        self.scaler = None
        self.filler = None
        
    def clean_data(self, df, time_col='time', value_col='value'):
        """清理时间序列数据"""
        try:
            # 确保时间列是datetime类型
            df[time_col] = pd.to_datetime(df[time_col])
            
            # 去除重复时间点
            df = df.drop_duplicates(subset=[time_col])
            
            # 按时间排序
            df = df.sort_values(time_col)
            
            # 检查并处理缺失值
            missing_count = df[value_col].isna().sum()
            if missing_count > 0:
                logger.info(f"发现 {missing_count} 个缺失值，将进行插值处理")
                df[value_col] = df[value_col].interpolate(method='linear')
            
            # 去除异常值（使用IQR方法）
            Q1 = df[value_col].quantile(0.25)
            Q3 = df[value_col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers_mask = (df[value_col] < lower_bound) | (df[value_col] > upper_bound)
            outliers_count = outliers_mask.sum()
            
            if outliers_count > 0:
                logger.info(f"发现 {outliers_count} 个异常值，将进行处理")
                # 用边界值替换异常值
                df.loc[df[value_col] < lower_bound, value_col] = lower_bound
                df.loc[df[value_col] > upper_bound, value_col] = upper_bound
            
            return df
            
        except Exception as e:
            logger.error(f"数据清理过程中出错: {str(e)}")
            raise
    
    def create_time_series(self, df, time_col='time', value_col='value', freq=None):
        """将DataFrame转换为Darts TimeSeries对象"""
        try:
            # 设置时间列为索引
            df_indexed = df.set_index(time_col)
            
            # 自动检测频率
            if freq is None:
                time_diff = df_indexed.index.to_series().diff().dropna()
                most_common_diff = time_diff.mode()[0]
                
                # 根据时间差确定频率
                if most_common_diff <= timedelta(minutes=1):
                    freq = 'T'  # 分钟
                elif most_common_diff <= timedelta(hours=1):
                    freq = 'H'  # 小时
                elif most_common_diff <= timedelta(days=1):
                    freq = 'D'  # 天
                else:
                    freq = 'W'  # 周
            
            # 创建TimeSeries对象
            series = TimeSeries.from_dataframe(
                df_indexed,
                value_cols=value_col,
                freq=freq
            )
            
            return series
            
        except Exception as e:
            logger.error(f"创建TimeSeries对象时出错: {str(e)}")
            raise
    
    def scale_data(self, series):
        """标准化数据"""
        try:
            self.scaler = Scaler()
            scaled_series = self.scaler.fit_transform(series)
            return scaled_series
        except Exception as e:
            logger.error(f"数据标准化时出错: {str(e)}")
            raise
    
    def inverse_scale_data(self, scaled_series):
        """反向标准化数据"""
        try:
            if self.scaler is None:
                raise ValueError("需要先调用scale_data方法")
            return self.scaler.inverse_transform(scaled_series)
        except Exception as e:
            logger.error(f"反向标准化时出错: {str(e)}")
            raise

class ModelEvaluator:
    """模型评估工具类"""
    
    @staticmethod
    def calculate_metrics(actual, predicted):
        """计算预测评估指标"""
        try:
            metrics = {}
            
            # 确保两个序列长度一致
            min_len = min(len(actual), len(predicted))
            actual_trimmed = actual[:min_len]
            predicted_trimmed = predicted[:min_len]
            
            # 计算各种评估指标
            metrics['mape'] = float(mape(actual_trimmed, predicted_trimmed))
            metrics['rmse'] = float(rmse(actual_trimmed, predicted_trimmed))
            metrics['mae'] = float(mae(actual_trimmed, predicted_trimmed))
            metrics['mse'] = float(mse(actual_trimmed, predicted_trimmed))
            
            # 计算方向准确率（预测趋势是否正确）
            actual_diff = np.diff(actual_trimmed.values().flatten())
            predicted_diff = np.diff(predicted_trimmed.values().flatten())
            direction_accuracy = np.mean(np.sign(actual_diff) == np.sign(predicted_diff))
            metrics['direction_accuracy'] = float(direction_accuracy)
            
            return metrics
            
        except Exception as e:
            logger.error(f"计算评估指标时出错: {str(e)}")
            return None
    
    @staticmethod
    def compare_models(results_dict):
        """比较多个模型的性能"""
        try:
            comparison = []
            
            for model_name, result in results_dict.items():
                if 'metrics' in result and result['metrics'] is not None:
                    comparison.append({
                        'model': model_name,
                        **result['metrics']
                    })
            
            # 按MAPE排序
            comparison.sort(key=lambda x: x['mape'])
            
            return comparison
            
        except Exception as e:
            logger.error(f"模型比较时出错: {str(e)}")
            return []

class DataGenerator:
    """时间序列数据生成器"""
    
    @staticmethod
    def generate_synthetic_data(length=365, start_date='2023-01-01', freq='D', 
                              trend_strength=0.1, seasonal_periods=[7, 30], 
                              noise_level=0.1, base_value=100):
        """生成合成时间序列数据"""
        try:
            dates = pd.date_range(start=start_date, periods=length, freq=freq)
            
            # 基础值
            values = np.full(length, base_value)
            
            # 添加趋势
            if trend_strength > 0:
                trend = np.linspace(0, trend_strength * base_value, length)
                values += trend
            
            # 添加季节性
            for period in seasonal_periods:
                seasonal_amplitude = base_value * 0.1  # 季节性振幅为基础值的10%
                seasonal = seasonal_amplitude * np.sin(2 * np.pi * np.arange(length) / period)
                values += seasonal
            
            # 添加噪声
            if noise_level > 0:
                noise = np.random.normal(0, noise_level * base_value, length)
                values += noise
            
            # 确保值为正数
            values = np.maximum(values, base_value * 0.1)
            
            df = pd.DataFrame({
                'time': dates,
                'value': values
            })
            
            return df
            
        except Exception as e:
            logger.error(f"生成合成数据时出错: {str(e)}")
            raise
    
    @staticmethod
    def add_external_factors(df, factor_type='marketing'):
        """为数据添加外部因素"""
        try:
            length = len(df)
            
            if factor_type == 'marketing':
                # 模拟营销支出数据
                marketing_spend = np.random.exponential(50, length)
                df['marketing_spend'] = marketing_spend
                
            elif factor_type == 'weather':
                # 模拟温度数据
                base_temp = 20
                seasonal_temp = 15 * np.sin(2 * np.pi * np.arange(length) / 365)
                daily_temp = np.random.normal(0, 3, length)
                temperature = base_temp + seasonal_temp + daily_temp
                df['temperature'] = temperature
                
            elif factor_type == 'economic':
                # 模拟经济指标
                economic_index = 100 + np.cumsum(np.random.normal(0, 1, length))
                df['economic_index'] = economic_index
            
            return df
            
        except Exception as e:
            logger.error(f"添加外部因素时出错: {str(e)}")
            raise

def format_response_data(series, forecast, validation=None, metrics=None, model_info=None):
    """格式化API响应数据"""
    try:
        response = {
            'historical': {
                'dates': series.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'values': series.values().flatten().tolist()
            },
            'forecast': {
                'dates': forecast.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'values': forecast.values().flatten().tolist()
            }
        }
        
        if validation is not None:
            response['validation'] = {
                'dates': validation.time_index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'values': validation.values().flatten().tolist()
            }
        
        if metrics is not None:
            response['metrics'] = metrics
            
        if model_info is not None:
            response['model_info'] = model_info
        
        return response
        
    except Exception as e:
        logger.error(f"格式化响应数据时出错: {str(e)}")
        raise

def validate_forecast_request(data):
    """验证预测请求参数"""
    try:
        # 检查必需参数
        if 'model' not in data:
            return False, "缺少模型参数"
        
        if 'periods' not in data:
            return False, "缺少预测周期参数"
        
        # 验证参数值
        periods = data.get('periods')
        if not isinstance(periods, int) or periods <= 0 or periods > 365:
            return False, "预测周期必须是1-365之间的整数"
        
        valid_models = ['exponential_smoothing', 'prophet', 'arima', 'four_theta']
        if data.get('model') not in valid_models:
            return False, f"不支持的模型类型，支持的模型: {', '.join(valid_models)}"
        
        return True, "参数验证通过"
        
    except Exception as e:
        return False, f"参数验证时出错: {str(e)}"