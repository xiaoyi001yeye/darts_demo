from abc import ABC, abstractmethod

class BaseModel(ABC):
    """时间序列预测模型的抽象基类"""
    
    @abstractmethod
    def get_name(self):
        """返回模型名称"""
        pass
    
    @abstractmethod
    def get_description(self):
        """返回模型描述"""
        pass
    
    @abstractmethod
    def get_parameter_config(self):
        """返回模型参数配置"""
        pass
    
    @abstractmethod
    def create_model(self, **params):
        """根据参数创建模型实例"""
        pass
    
    @abstractmethod
    def fit(self, model, train_data):
        """训练模型"""
        pass
    
    @abstractmethod
    def predict(self, model, periods):
        """使用模型进行预测"""
        pass