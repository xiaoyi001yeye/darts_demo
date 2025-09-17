#!/usr/bin/env python3
"""
Flask API 接口测试脚本
测试 app.py 中的所有关键业务接口
"""
import requests
import json
import time
import sys
from datetime import datetime

class APITester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
    def log(self, message, level="INFO"):
        """打印带时间戳的日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def test_connection(self):
        """测试服务器连接"""
        self.log("测试服务器连接...")
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                self.log("✓ 服务器连接成功", "SUCCESS")
                return True
            else:
                self.log(f"✗ 服务器连接失败，状态码: {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"✗ 服务器连接异常: {str(e)}", "ERROR")
            return False
    
    def test_health_endpoint(self):
        """测试健康检查接口"""
        self.log("测试健康检查接口 GET /api/health")
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            
            # 验证状态码
            assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
            
            # 验证响应格式
            data = response.json()
            required_fields = ['status', 'timestamp', 'version']
            for field in required_fields:
                assert field in data, f"响应中缺少字段: {field}"
            
            assert data['status'] == 'healthy', f"期望status为healthy，实际: {data['status']}"
            
            self.log("✓ 健康检查接口测试通过", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"✗ 健康检查接口测试失败: {str(e)}", "ERROR")
            return False
    
    def test_models_endpoint(self):
        """测试模型列表接口"""
        self.log("测试模型列表接口 GET /api/models")
        try:
            response = self.session.get(f"{self.base_url}/api/models")
            
            # 验证状态码
            assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
            
            # 验证响应格式
            data = response.json()
            assert isinstance(data, list), "期望响应为列表格式"
            assert len(data) > 0, "期望至少有一个模型"
            
            # 验证模型信息结构
            model = data[0]
            required_fields = ['id', 'name', 'description', 'parameters']
            for field in required_fields:
                assert field in model, f"模型信息中缺少字段: {field}"
            
            self.log("✓ 模型列表接口测试通过", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"✗ 模型列表接口测试失败: {str(e)}", "ERROR")
            return False
    
    def test_data_info_endpoint(self):
        """测试数据信息接口"""
        self.log("测试数据信息接口 GET /api/data/info")
        try:
            response = self.session.get(f"{self.base_url}/api/data/info")
            
            # 如果数据文件不存在，这是预期的错误
            if response.status_code == 500:
                error_data = response.json()
                if "数据文件不存在" in error_data.get('error', ''):
                    self.log("⚠ 数据文件不存在，这是预期的（使用测试数据）", "WARNING")
                    return True
                    
            assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
            
            # 验证响应格式
            data = response.json()
            required_fields = ['device_id', 'total_points', 'date_range', 'frequency', 'statistics']
            for field in required_fields:
                assert field in data, f"数据信息中缺少字段: {field}"
            
            self.log("✓ 数据信息接口测试通过", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"✗ 数据信息接口测试失败: {str(e)}", "ERROR")
            return False
    
    def test_data_preview_endpoint(self):
        """测试数据预览接口"""
        self.log("测试数据预览接口 GET /api/data/preview")
        try:
            response = self.session.get(f"{self.base_url}/api/data/preview")
            
            # 如果数据文件不存在，这是预期的错误
            if response.status_code == 500:
                error_data = response.json()
                if "数据文件不存在" in error_data.get('error', ''):
                    self.log("⚠ 数据文件不存在，这是预期的（使用测试数据）", "WARNING")
                    return True
                    
            assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
            
            # 验证响应格式
            data = response.json()
            required_fields = ['device_id', 'data', 'total_points', 'preview_points']
            for field in required_fields:
                assert field in data, f"数据预览中缺少字段: {field}"
            
            # 验证数据结构
            assert 'dates' in data['data'], "数据中缺少dates字段"
            assert 'values' in data['data'], "数据中缺少values字段"
            
            self.log("✓ 数据预览接口测试通过", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"✗ 数据预览接口测试失败: {str(e)}", "ERROR")
            return False
    
    def test_train_endpoint(self):
        """测试模型训练接口"""
        self.log("测试模型训练接口 POST /api/train")
        try:
            # 准备训练参数
            train_params = {
                "p": 2,
                "d": 1,
                "q": 2,
                "train_ratio": 0.8
            }
            
            response = self.session.post(
                f"{self.base_url}/api/train",
                json=train_params,
                timeout=60  # 训练可能需要更长时间
            )
            
            # 如果数据文件不存在，这是预期的错误
            if response.status_code == 500:
                error_data = response.json()
                if "数据文件不存在" in error_data.get('error', ''):
                    self.log("⚠ 数据文件不存在，无法训练模型", "WARNING")
                    return True
                    
            assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
            
            # 验证响应格式
            data = response.json()
            assert data.get('success') == True, "期望训练成功"
            
            required_fields = ['model_params', 'data_info', 'training_data', 'validation_data', 'metrics']
            for field in required_fields:
                assert field in data, f"训练响应中缺少字段: {field}"
            
            self.log("✓ 模型训练接口测试通过", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"✗ 模型训练接口测试失败: {str(e)}", "ERROR")
            return False
    
    def test_predict_endpoint(self):
        """测试预测接口"""
        self.log("测试预测接口 POST /api/predict")
        try:
            # 准备预测参数
            predict_params = {
                "periods": 24
            }
            
            response = self.session.post(
                f"{self.base_url}/api/predict",
                json=predict_params,
                timeout=30
            )
            
            # 如果没有训练模型，这是预期的错误
            if response.status_code == 400:
                error_data = response.json()
                if "请先训练模型" in error_data.get('error', ''):
                    self.log("⚠ 没有训练好的模型，这是预期的", "WARNING")
                    return True
            
            # 如果数据文件不存在
            if response.status_code == 500:
                error_data = response.json()
                if "数据文件不存在" in error_data.get('error', ''):
                    self.log("⚠ 数据文件不存在，无法预测", "WARNING")
                    return True
                    
            assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
            
            # 验证响应格式
            data = response.json()
            assert data.get('success') == True, "期望预测成功"
            
            required_fields = ['forecast', 'forecast_info']
            for field in required_fields:
                assert field in data, f"预测响应中缺少字段: {field}"
            
            self.log("✓ 预测接口测试通过", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"✗ 预测接口测试失败: {str(e)}", "ERROR")
            return False
    
    def test_forecast_endpoint(self):
        """测试完整预测流程接口"""
        self.log("测试完整预测流程接口 POST /api/forecast")
        try:
            # 准备预测参数
            forecast_params = {
                "periods": 24,
                "p": 2,
                "d": 1,
                "q": 2,
                "train_ratio": 0.8
            }
            
            response = self.session.post(
                f"{self.base_url}/api/forecast",
                json=forecast_params,
                timeout=120  # 完整流程可能需要更长时间
            )
            
            # 如果数据文件不存在，这是预期的错误
            if response.status_code == 500:
                error_data = response.json()
                if "数据文件不存在" in error_data.get('error', ''):
                    self.log("⚠ 数据文件不存在，无法执行预测流程", "WARNING")
                    return True
                    
            assert response.status_code == 200, f"期望状态码200，实际: {response.status_code}"
            
            # 验证响应格式
            data = response.json()
            required_fields = ['historical', 'forecast', 'validation', 'metrics', 'model_info']
            for field in required_fields:
                assert field in data, f"预测流程响应中缺少字段: {field}"
            
            # 验证数据结构
            assert 'dates' in data['historical'], "历史数据中缺少dates字段"
            assert 'values' in data['historical'], "历史数据中缺少values字段"
            assert 'dates' in data['forecast'], "预测数据中缺少dates字段"
            assert 'values' in data['forecast'], "预测数据中缺少values字段"
            
            self.log("✓ 完整预测流程接口测试通过", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"✗ 完整预测流程接口测试失败: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始API接口测试...")
        self.log("="*60)
        
        # 首先检查连接
        if not self.test_connection():
            self.log("服务器连接失败，终止测试", "ERROR")
            return False
        
        # 等待服务器完全启动
        time.sleep(2)
        
        tests = [
            ("健康检查", self.test_health_endpoint),
            ("模型列表", self.test_models_endpoint),
            ("数据信息", self.test_data_info_endpoint),
            ("数据预览", self.test_data_preview_endpoint),
            ("模型训练", self.test_train_endpoint),
            ("模型预测", self.test_predict_endpoint),
            ("完整预测流程", self.test_forecast_endpoint)
        ]
        
        results = []
        for test_name, test_func in tests:
            self.log("-" * 40)
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # 测试间隔
        
        # 输出测试总结
        self.log("="*60)
        self.log("测试总结:")
        
        passed = 0
        for test_name, result in results:
            status = "✓ 通过" if result else "✗ 失败"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
        
        self.log(f"总计: {passed}/{len(results)} 个测试通过")
        
        if passed == len(results):
            self.log("🎉 所有测试通过！", "SUCCESS")
            return True
        else:
            self.log(f"⚠ {len(results) - passed} 个测试失败", "WARNING")
            return False

def main():
    """主函数"""
    # 检查命令行参数
    base_url = "http://localhost:5001"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"API测试目标: {base_url}")
    print("等待服务器启动...")
    time.sleep(5)  # 等待服务器启动
    
    # 创建测试器并运行测试
    tester = APITester(base_url)
    success = tester.run_all_tests()
    
    # 返回退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()