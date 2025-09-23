from models.base_model import BaseModel, ParameterConfig
from darts.models import AutoARIMA as DartsAutoARIMA

class AutoARIMAModel(BaseModel):
    """AutoARIMA模型实现"""

    def get_name(self):
        return "auto_arima"

    def get_description(self):
        return "AutoARIMA (自动选择最佳ARIMA参数)"

    def get_parameter_config(self):
        return {
            'season_length': ParameterConfig('number', default=12, min=1, max=24, description='季节性周期', index=1),
            'train_ratio': ParameterConfig('number', default=0.8, min=0.5, max=0.95, step=0.05, description='训练集比例', index=2),
            'confidence_level': ParameterConfig('number', default=0.95, min=0.8, max=0.99, step=0.01, description='置信水平', index=3),
            'num_samples': ParameterConfig('number', default=1, min=1, max=1000, description='采样数量', index=4)
        }

    def create_model(self, **params):
        # 提取AutoARIMA参数
        season_length = int(params.get('season_length', 12))

        # 创建模型实例
        model = DartsAutoARIMA(
            season_length=season_length
        )

        # 保存置信水平参数到模型实例
        model.confidence_level = params.get('confidence_level', 0.95)
        # 保存num_samples参数到模型实例
        model.num_samples = int(params.get('num_samples', 1))

        return model

    def fit(self, model, train_data, future_covariates=None):
        """添加对协变量的支持"""
        model.fit(train_data, future_covariates=future_covariates)
        return model

    def predict(self, model, periods, future_covariates=None):
        # 使用模型实例中保存的num_samples参数
        forecast = model.predict(
            periods,
            num_samples=getattr(model, 'num_samples', 1),
            future_covariates=future_covariates
        )
        return forecast
