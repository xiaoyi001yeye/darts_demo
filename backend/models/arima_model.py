from models.base_model import BaseModel
from darts.models import ARIMA

class ARIMAModel(BaseModel):
    """ARIMA模型实现"""
    
    def get_name(self):
        return "arima"
    
    def get_description(self):
        return "ARIMA (自回归积分滑动平均)"
    
    def get_parameter_config(self):
        return {
            'p': {'type': 'number', 'default': 2, 'min': 0, 'max': 5, 'description': '自回归阶数'},
            'd': {'type': 'number', 'default': 1, 'min': 0, 'max': 2, 'description': '差分阶数'},
            'q': {'type': 'number', 'default': 2, 'min': 0, 'max': 5, 'description': '移动平均阶数'},
            'train_ratio': {'type': 'number', 'default': 0.8, 'min': 0.5, 'max': 0.95, 'step': 0.05, 'description': '训练集比例'},
            'trend': {'type': 'select', 'options': ['n', 'c', 't', 'ct'], 'default': 'n', 'description': '趋势参数'},
            'seasonal_order_P': {'type': 'number', 'default': 0, 'min': 0, 'max': 3, 'description': '季节性自回归阶数'},
            'seasonal_order_D': {'type': 'number', 'default': 0, 'min': 0, 'max': 2, 'description': '季节性差分阶数'},
            'seasonal_order_Q': {'type': 'number', 'default': 0, 'min': 0, 'max': 3, 'description': '季节性移动平均阶数'},
            'seasonal_periods': {'type': 'number', 'default': 24, 'min': 1, 'max': 168, 'description': '季节性周期(小时)'}
        }
    
    def create_model(self, **params):
        p = int(params.get('p', 2))
        d = int(params.get('d', 1))
        q = int(params.get('q', 2))
        trend = params.get('trend', 'n')
        #             seasonal_order_P = int(data.get('seasonal_order_P', 0))
        #             seasonal_order_D = int(data.get('seasonal_order_D', 0))
        #             seasonal_order_Q = int(data.get('seasonal_order_Q', 0))
        #             seasonal_periods = int(data.get('seasonal_periods', 24))
        # 构建季节性参数
        #             seasonal_order = (seasonal_order_P, seasonal_order_D, seasonal_order_Q, seasonal_periods)

        return ARIMA(p=p, d=d, q=q, trend=trend)
    
    def fit(self, model, train_data):
        model.fit(train_data)
        return model
    
    def predict(self, model, periods):
        return model.predict(periods)