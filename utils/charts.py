import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_top_currencies_chart(df, base_currency, n=10):
    """Создает график топ N валют"""
    top = df[df['Валюта'] != base_currency].head(n)
    fig = px.bar(
        top,
        x='Курс',
        y='Валюта',
        orientation='h',
        title=f'Топ-{n} валют относительно {base_currency}',
        color='Курс',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(height=500)
    return fig

def create_historical_chart(historical_data, currency, base_currency):
    """Создает график исторических данных"""
    if historical_data is None or len(historical_data) == 0:
        return None
    
    fig = px.line(
        historical_data,
        x='date',
        y='rate',
        title=f'Курс {currency} к {base_currency} за последние 30 дней',
        markers=True
    )
    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title=f"Курс ({currency}/{base_currency})",
        hovermode='x unified'
    )
    return fig

def create_world_map(df):
    """Создает карту мира с курсами валют"""
    # ISO коды валют для карты (упрощенная версия)
    currency_to_country = {
        'USD': 'USA', 'EUR': 'FRA', 'GBP': 'GBR', 'JPY': 'JPN',
        'CNY': 'CHN', 'INR': 'IND', 'RUB': 'RUS', 'CAD': 'CAN',
        'AUD': 'AUS', 'CHF': 'CHE', 'BRL': 'BRA', 'KRW': 'KOR'
    }
    
    map_data = []
    for _, row in df.iterrows():
        currency = row['Валюта']
        if currency in currency_to_country:
            map_data.append({
                'country': currency_to_country[currency],
                'currency': currency,
                'rate': row['Курс']
            })
    
    if not map_data:
        return None
    
    map_df = pd.DataFrame(map_data)
    
    fig = px.choropleth(
        map_df,
        locations='country',
        locationmode='country names',
        color='rate',
        hover_name='currency',
        hover_data={'rate': ':.4f'},
        title='Курсы валют на карте мира',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(height=500)
    return fig

def create_comparison_chart(df, currency1, currency2):
    """Создает график сравнения двух валют"""
    rate1 = df[df['Валюта'] == currency1]['Курс'].values[0]
    rate2 = df[df['Валюта'] == currency2]['Курс'].values[0]
    
    fig = go.Figure(data=[
        go.Bar(name=currency1, x=[currency1], y=[rate1], marker_color='#1f77b4'),
        go.Bar(name=currency2, x=[currency2], y=[rate2], marker_color='#ff7f0e')
    ])
    fig.update_layout(
        title=f'Сравнение курсов: {currency1} vs {currency2}',
        yaxis_title="Курс относительно базовой валюты"
    )
    return fig