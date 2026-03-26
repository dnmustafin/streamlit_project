import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

def check_alerts(current_df, historical_data_cache):
    """Проверяет и генерирует алерты"""
    alerts = []
    
    # Сохраняем предыдущие курсы в сессии
    if 'prev_rates' not in st.session_state:
        st.session_state.prev_rates = {}
    
    for _, row in current_df.iterrows():
        currency = row['Валюта']
        current_rate = row['Курс']
        
        # Проверяем изменение за сутки
        if currency in st.session_state.prev_rates:
            prev_rate = st.session_state.prev_rates[currency]
            if prev_rate > 0:
                change = ((current_rate - prev_rate) / prev_rate) * 100
                if abs(change) > 3:  # Изменение более 3%
                    alerts.append({
                        'currency': currency,
                        'change': change,
                        'type': 'daily',
                        'message': f"⚠️ {currency}: {change:+.2f}% за сутки!"
                    })
        
        # Проверка исторических аномалий
        if currency in historical_data_cache and historical_data_cache[currency] is not None:
            hist_data = historical_data_cache[currency]
            if len(hist_data) > 10:
                mean = hist_data['rate'].mean()
                std = hist_data['rate'].std()
                z_score = abs(current_rate - mean) / std if std > 0 else 0
                
                if z_score > 2:
                    alerts.append({
                        'currency': currency,
                        'z_score': z_score,
                        'type': 'anomaly',
                        'message': f"🚨 {currency}: Аномальное движение! Отклонение {z_score:.1f}σ от нормы"
                    })
        
        # Обновляем предыдущие курсы
        st.session_state.prev_rates[currency] = current_rate
    
    return alerts