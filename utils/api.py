import requests
import pandas as pd
import streamlit as st

@st.cache_data(ttl=3600)
def fetch_currency_rates(base_currency="USD"):
    """Получает актуальные курсы валют с резервными API"""
    
    apis = [
        {
            "name": "Frankfurter",
            "url": f"https://api.frankfurter.app/latest?from={base_currency}",
            "parser": lambda data: (data['rates'], data['date'])
        },
        {
            "name": "ExchangeRate-API",
            "url": f"https://api.exchangerate-api.com/v4/latest/{base_currency}",
            "parser": lambda data: (data['rates'], data['date'])
        }
    ]
    
    for api in apis:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(api["url"], headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            rates, date = api["parser"](data)
            
            df = pd.DataFrame(list(rates.items()), columns=['Валюта', 'Курс'])
            df = df.sort_values('Курс', ascending=False)
            df_base = pd.DataFrame([[base_currency, 1.0]], columns=['Валюта', 'Курс'])
            df = pd.concat([df_base, df], ignore_index=True)
            
            return df, date, api["name"]
            
        except Exception as e:
            continue
    
    # Демо-данные
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
