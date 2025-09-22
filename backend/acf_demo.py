import matplotlib.pyplot as plt
from darts import TimeSeries
from darts.datasets import AirPassengersDataset
from darts.utils.statistics import plot_acf, plot_pacf

# 1. 加载一个示例时间序列数据集
# Darts提供了许多内置数据集，方便进行测试和演示
series = AirPassengersDataset().load()

# 2. 绘制原始时间序列以进行初步目视检查
# 我们可以观察到明显的趋势和季节性，这表明它是一个非平稳序列
plt.figure(figsize=(10, 6))
series.plot(label='原始乘客数数据')
plt.title('AirPassengers数据集')
plt.show()

# 3. 对原始（非平稳）时间序列绘制ACF和PACF
# 由于存在趋势和季节性，ACF图将显示缓慢衰减，这是一种非平稳行为的典型特征
plt.figure(figsize=(12, 6))
plot_acf(series, m=12, title='ACF of Non-Stationary Series')
plt.show()

# PACF图也可能显示非平稳序列的特征
plt.figure(figsize=(12, 6))
plot_pacf(series, method='ywadjusted', max_lag=40, title='PACF of Non-Stationary Series')
plt.show()

# 4. 对时间序列进行差分以实现平稳性
# 差分是移除趋势和季节性的常见方法
diff_series = series.diff(periods=1)

# 移除差分后产生的第一个NaN值
diff_series = diff_series.dropna()

# 5. 对差分后的（平稳）时间序列绘制ACF和PACF
# 现在，图表将更清晰地显示自回归和移动平均过程的特征，可用于模型选择
plt.figure(figsize=(12, 6))
plot_acf(diff_series, title='ACF of Differenced Series')
plt.show()

plt.figure(figsize=(12, 6))
plot_pacf(diff_series, method='ywadjusted', title='PACF of Differenced Series')
plt.show()