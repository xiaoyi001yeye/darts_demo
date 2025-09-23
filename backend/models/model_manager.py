from models.arima_model import ARIMAModel
from models.prophet_model import ProphetModel
from models.auto_arima_model import AutoARIMAModel

class ModelManager:
    """模型管理器，用于注册和管理所有预测模型"""
    
    def __init__(self):
        self.models = {}
        self._register_default_models()
    
    def _register_default_models(self):
        """注册默认模型"""
        self.register_model(ARIMAModel())
        self.register_model(ProphetModel())
        self.register_model(AutoARIMAModel())
    
    def register_model(self, model):
        """注册新模型"""
        self.models[model.get_name()] = model
    
    def get_model(self, model_name):
        """获取模型实例"""
        return self.models.get(model_name)
    
    def get_available_models(self):
        """获取所有可用模型信息"""
        model_list = []
        for name, model in self.models.items():
            model_list.append({
                'id': name,
                'name': model.get_description(),
                'description': f'专用于存储空间使用率预测的{model.get_description()}模型' if name == 'arima' 
                              else 'Facebook开发的基于加法模型的时间序列预测模型，适合有季节性效应的数据'
            })
        return model_list
    
    def get_model_parameters(self, model_name):
        """获取指定模型的参数配置"""
        model = self.models.get(model_name)
        if model:
            return model.get_parameter_config()
        return None
