from abc import ABC, abstractmethod

class ParameterConfig:
    """参数配置类，用于描述模型参数的配置信息"""
    
    def __init__(self, param_type, default=None, description="", **kwargs):
        self.type = param_type
        self.default = default
        self.description = description
        # 根据参数类型存储额外属性
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """将参数配置转换为字典格式"""
        result = {
            'type': self.type,
            'default': self.default,
            'description': self.description
        }
        
        # 添加其他属性
        for key, value in self.__dict__.items():
            if key not in ['type', 'default', 'description']:
                result[key] = value
                
        return result

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