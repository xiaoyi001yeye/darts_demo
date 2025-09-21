from models.base_model import BaseModel, ParameterConfig
from darts.models import ARIMA

class ARIMAModel(BaseModel):
    """ARIMA模型实现"""
    
    def get_name(self):
        return "arima"
    
    def get_description(self):
        return "ARIMA (自回归积分滑动平均)"
    
    def get_parameter_config(self):
        return {
            'p': ParameterConfig('number', default=2, min=0, max=5, description='自回归阶数'),
            'd': ParameterConfig('number', default=1, min=0, max=2, description='差分阶数'),
            'q': ParameterConfig('number', default=2, min=0, max=5, description='移动平均阶数'),
            'train_ratio': ParameterConfig('number', default=0.8, min=0.5, max=0.95, step=0.05, description='训练集比例'),
            'trend': ParameterConfig('select', default='n', options=['n', 'c', 't', 'ct'], description='趋势参数'),
            'seasonal_order_P': ParameterConfig('number', default=0, min=0, max=3, description='季节性自回归阶数'),
            'seasonal_order_D': ParameterConfig('number', default=0, min=0, max=2, description='季节性差分阶数'),
            'seasonal_order_Q': ParameterConfig('number', default=0, min=0, max=3, description='季节性移动平均阶数'),
            'seasonal_periods': ParameterConfig('number', default=24, min=1, max=168, description='季节性周期(小时)'),
            'confidence_level': ParameterConfig('number', default=0.95, min=0.8, max=0.99, step=0.01, description='置信水平'),
            'num_samples': ParameterConfig('number', default=1, min=1, max=1000, description='采样数量')
        }
    
    def create_model(self, **params):
        p = int(params.get('p', 2))
        d = int(params.get('d', 1))
        q = int(params.get('q', 2))
        trend = params.get('trend', 'n')
        seasonal_order_P = int(params.get('seasonal_order_P', 0))
        seasonal_order_D = int(params.get('seasonal_order_D', 0))
        seasonal_order_Q = int(params.get('seasonal_order_Q', 0))
        seasonal_periods = int(params.get('seasonal_periods', 24))
        # 构建季节性参数
        seasonal_order = (seasonal_order_P, seasonal_order_D, seasonal_order_Q, seasonal_periods)
        
        # 创建模型实例
        model = ARIMA(p=p, d=d, q=q, trend=trend, seasonal_order=seasonal_order)
        
        # 保存置信水平参数到模型实例
        model.confidence_level = params.get('confidence_level', 0.95)
        # 保存num_samples参数到模型实例
        model.num_samples = int(params.get('num_samples', 1))
        
        return model
    
    def fit(self, model, train_data):
        model.fit(train_data)
        return model
    
    def predict(self, model, periods):
        # 使用模型实例中保存的num_samples参数
        forecast = model.predict(periods, num_samples=getattr(model, 'num_samples', 1))

        # 添加置信区间计算（如果模型支持）
        if hasattr(model, 'predict_interval'):
            # 对于支持置信区间的模型
            forecast_interval = model.predict_interval(periods, alpha=0.05)  # 95%置信区间
            # 日志记录置信区间数据
            print(f"ARIMA模型置信区间: {forecast_interval}")
            return forecast, forecast_interval
        else:
            # 对于不支持置信区间的模型，返回None作为区间
            return forecast, None