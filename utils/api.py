import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os
import json

@st.cache_data(ttl=3600)
def fetch_currency_rates(base_currency="USD"):
    """Получает актуальные курсы валют"""
    headers = {'User-Agent': 'Mozilla/5.0'}

    frankfurter_rates = None
    frankfurter_date = None
    fallback_rates = None
    fallback_date = None

    try:
        response = requests.get(
            f"https://api.frankfurter.app/latest?from={base_currency}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        frankfurter_rates = data.get('rates', {})
        frankfurter_date = data.get('date')
    except Exception:
        pass

    try:
        response = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{base_currency}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        fallback_rates = data.get('rates', {})
        fallback_date = data.get('date')
    except Exception:
        pass

    # Базовый источник: Frankfurter. Если в нем нет RUB, дозаполняем из fallback.
    if frankfurter_rates:
        merged_rates = dict(frankfurter_rates)
        source_name = "Frankfurter"
        if 'RUB' not in merged_rates and fallback_rates and 'RUB' in fallback_rates:
            merged_rates['RUB'] = fallback_rates['RUB']
            source_name = "Frankfurter + ExchangeRate-API (RUB)"

        df = pd.DataFrame(list(merged_rates.items()), columns=['Валюта', 'Курс'])
        df = df.sort_values('Курс', ascending=False)
        df_base = pd.DataFrame([[base_currency, 1.0]], columns=['Валюта', 'Курс'])
        df = pd.concat([df_base, df], ignore_index=True)

        save_to_cache(df, base_currency, frankfurter_date or fallback_date)
        return df, (frankfurter_date or fallback_date), source_name

    # Если основной источник недоступен, используем fallback целиком.
    if fallback_rates:
        df = pd.DataFrame(list(fallback_rates.items()), columns=['Валюта', 'Курс'])
        df = df.sort_values('Курс', ascending=False)
        df_base = pd.DataFrame([[base_currency, 1.0]], columns=['Валюта', 'Курс'])
        df = pd.concat([df_base, df], ignore_index=True)

        save_to_cache(df, base_currency, fallback_date)
        return df, fallback_date, "ExchangeRate-API"
    
    cached = load_from_cache(base_currency)
    if cached:
        return cached['df'], cached['date'], "Кэш"
    
    demo_rates = {
        "EUR": 0.92, "GBP": 0.79, "JPY": 150.23, "CAD": 1.35,
        "CHF": 0.88, "CNY": 7.19, "INR": 83.12, "AUD": 1.52,
        "RUB": 92.45, "BRL": 5.02, "KRW": 1334.56, "SGD": 1.34
    }
    
    df = pd.DataFrame(list(demo_rates.items()), columns=['Валюта', 'Курс'])
    df = df.sort_values('Курс', ascending=False)
    df_base = pd.DataFrame([[base_currency, 1.0]], columns=['Валюта', 'Курс'])
    df = pd.concat([df_base, df], ignore_index=True)
    
    return df, "Демонстрационные данные", "Local Demo"

@st.cache_data(ttl=3600)
def get_historical_rates(currency, base="USD", days=30):
    """Получает исторические данные одним запросом (быстро!)"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={base}&to={currency}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'rates' in data:
            dates = []
            rates = []
            for date, rates_data in data['rates'].items():
                if currency in rates_data:
                    dates.append(date)
                    rates.append(rates_data[currency])
            
            if dates:
                df = pd.DataFrame({'date': dates, 'rate': rates})
                return df.sort_values('date')
    except Exception as e:
        print(f"Error fetching historical data: {e}")
    
    return None

def save_to_cache(df, base_currency, date):
    """Сохраняет данные в кэш"""
    cache_dir = "data/cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_file = f"{cache_dir}/rates_{base_currency}.json"
    data = {
        'df': df.to_dict(),
        'date': date,
        'base': base_currency
    }
    with open(cache_file, 'w') as f:
        json.dump(data, f)

def load_from_cache(base_currency):
    """Загружает данные из кэша"""
    cache_file = f"data/cache/rates_{base_currency}.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            data = json.load(f)
            return {
                'df': pd.DataFrame(data['df']),
                'date': data['date']
            }
    return None