from models.base_model import BaseModel, ParameterConfig
from darts.models import Prophet

class ProphetModel(BaseModel):
    """Prophet模型实现"""
    
    def get_name(self):
        return "prophet"
    
    def get_description(self):
        return "Prophet (时间序列预测模型)"
    
    def get_parameter_config(self):
        return {
            'seasonality_mode': ParameterConfig('select', default='additive', options=['additive', 'multiplicative'], description='季节性模式'),
            'seasonality_prior_scale': ParameterConfig('number', default=10.0, min=0.01, max=100.0, step=0.01, description='季节性先验尺度'),
            'changepoint_prior_scale': ParameterConfig('number', default=0.05, min=0.001, max=1.0, step=0.001, description='趋势变化点先验尺度'),
            'holidays_prior_scale': ParameterConfig('number', default=10.0, min=0.01, max=100.0, step=0.01, description='节假日先验尺度'),
            'yearly_seasonality': ParameterConfig('boolean', default=True, description='是否启用年度季节性'),
            'weekly_seasonality': ParameterConfig('boolean', default=True, description='是否启用周度季节性'),
            'daily_seasonality': ParameterConfig('boolean', default=False, description='是否启用日度季节性'),
            'train_ratio': ParameterConfig('number', default=0.8, min=0.5, max=0.95, step=0.05, description='训练集比例')
        }
    
    def create_model(self, **params):
        return Prophet(
            seasonality_mode=params.get('seasonality_mode', 'additive'),
            seasonality_prior_scale=float(params.get('seasonality_prior_scale', 10.0)),
            yearly_seasonality=params.get('yearly_seasonality', True),
            weekly_seasonality=params.get('weekly_seasonality', True),
            daily_seasonality=params.get('daily_seasonality', False)
        )
    
    def fit(self, model, train_data):
        model.fit(train_data)
        return model
    
    def predict(self, model, periods):
        return model.predict(periods)