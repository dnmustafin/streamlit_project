import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

def predict_rate(historical_data, days_ahead=7):
    """Предсказывает курс на основе линейной регрессии"""
    if historical_data is None or len(historical_data) < 7:
        return None, None
    
    df = historical_data.copy()
    df['days'] = range(len(df))
    
    # Линейная регрессия
    model = LinearRegression()
    model.fit(df[['days']], df['rate'])
    
    future_days = np.array(range(len(df), len(df) + days_ahead)).reshape(-1, 1)
    linear_pred = model.predict(future_days)
    
    # Полиномиальная регрессия (более сложная)
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(df[['days']])
    model_poly = LinearRegression()
    model_poly.fit(X_poly, df['rate'])
    
    X_future_poly = poly.transform(future_days)
    poly_pred = model_poly.predict(X_future_poly)
    
    # Комбинированный прогноз (усреднение)
    combined_pred = (linear_pred + poly_pred) / 2
    
    # Доверительный интервал
    residuals = df['rate'] - model.predict(df[['days']])
    std_dev = np.std(residuals)
    upper_bound = combined_pred + 1.96 * std_dev
    lower_bound = combined_pred - 1.96 * std_dev
    
    return combined_pred, (lower_bound, upper_bound)

def detect_anomaly(historical_data, current_rate):
    """Обнаруживает аномалии в курсе"""
    if historical_data is None or len(historical_data) < 10:
        return False
    
    mean = historical_data['rate'].mean()
    std = historical_data['rate'].std()
    
    z_score = abs(current_rate - mean) / std
    
    return z_score > 2  # Аномалия если отклонение > 2 сигм