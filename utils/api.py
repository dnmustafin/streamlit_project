import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import os
import json


def _normalize_rates_dict(rates):
    """Нормализует словарь курсов до формата ISO-like 3-letter кодов."""
    if not isinstance(rates, dict):
        return {}

    normalized = {}
    for code, value in rates.items():
        try:
            code_up = str(code).upper()
            rate = float(value)
        except (TypeError, ValueError):
            continue

        # Оставляем только буквенные 3-буквенные коды и корректные значения.
        if len(code_up) == 3 and code_up.isalpha() and rate > 0:
            normalized[code_up] = rate

    return normalized

@st.cache_data(ttl=3600)
def fetch_currency_rates(base_currency="USD"):
    """Получает актуальные курсы валют из надежных источников с fallback."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    base_currency = base_currency.upper()

    open_er_rates = None
    open_er_date = None
    frankfurter_rates = None
    frankfurter_date = None
    fawaz_rates = None
    fawaz_date = None

    try:
        response = requests.get(
            f"https://open.er-api.com/v6/latest/{base_currency}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        open_er_rates = _normalize_rates_dict(data.get('rates', {}))
        open_er_date = data.get('time_last_update_utc') or data.get('time_last_update_unix')
    except Exception:
        pass

    try:
        response = requests.get(
            f"https://api.frankfurter.app/latest?from={base_currency}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        frankfurter_rates = _normalize_rates_dict(data.get('rates', {}))
        frankfurter_date = data.get('date')
    except Exception:
        pass

    try:
        response = requests.get(
            f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base_currency.lower()}.json",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        fawaz_rates = _normalize_rates_dict(data.get(base_currency.lower(), {}))
        fawaz_date = data.get('date')
    except Exception:
        pass

    # Приоритет: open.er-api -> Frankfurter -> Fawaz (как fallback для полноты).
    if open_er_rates or frankfurter_rates or fawaz_rates:
        merged_rates = {}
        source_parts = []
        latest_date = None
        trusted_codes = set()

        if open_er_rates:
            merged_rates.update(open_er_rates)
            trusted_codes.update(open_er_rates.keys())
            source_parts.append("open.er-api")
            latest_date = open_er_date
        if frankfurter_rates:
            for c, r in frankfurter_rates.items():
                merged_rates.setdefault(c, r)
            trusted_codes.update(frankfurter_rates.keys())
            source_parts.append("Frankfurter")
            latest_date = latest_date or frankfurter_date
        if fawaz_rates:
            for c, r in fawaz_rates.items():
                # Не засоряем список криптотикерами: добавляем только
                # "доверенные" валюты и RUB как критичный кейс.
                if c in trusted_codes or c == "RUB":
                    merged_rates.setdefault(c, r)
            source_parts.append("Fawaz API")
            latest_date = latest_date or fawaz_date

        merged_rates.pop(base_currency, None)

        df = pd.DataFrame(list(merged_rates.items()), columns=['Валюта', 'Курс'])
        df = df.sort_values('Курс', ascending=False)
        df_base = pd.DataFrame([[base_currency, 1.0]], columns=['Валюта', 'Курс'])
        df = pd.concat([df_base, df], ignore_index=True)

        save_to_cache(df, base_currency, latest_date)
        return df, latest_date, " + ".join(source_parts)
    
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
    """Получает историю курса с fallback на архивный источник."""
    currency = currency.upper()
    base = base.upper()
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    url = f"https://api.frankfurter.app/{start_date}..{end_date}?from={base}&to={currency}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            # У Frankfurter нет части валютных пар (например USD->RUB).
            response = None
        else:
            response.raise_for_status()
        if response is None:
            raise ValueError("Frankfurter pair is unavailable")
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
    except Exception:
        pass

    # Fallback: архивные ежедневные курсы (полнее по покрытию, но медленнее).
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        records = []
        start_dt = datetime.now() - timedelta(days=days)
        for i in range(days + 1):
            day = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            fallback_url = (
                f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{day}/v1/currencies/{base.lower()}.json"
            )
            response = requests.get(fallback_url, headers=headers, timeout=8)
            if response.status_code != 200:
                continue

            data = response.json()
            rates = data.get(base.lower(), {})
            if currency.lower() in rates:
                records.append({
                    'date': day,
                    'rate': float(rates[currency.lower()])
                })

        if records:
            return pd.DataFrame(records).sort_values('date')
    except Exception:
        pass
    
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