import streamlit as st
import pandas as pd
import plotly.express as plt
from utils.api import fetch_currency_rates

# Настройка страницы
st.set_page_config(
    page_title="Курсы валют",
    page_icon="💱",
    layout="wide"
)

st.title("💱 Дашборд курсов валют")
st.markdown("---")

# Сайдбар
with st.sidebar:
    st.header("⚙️ Настройки")
    
    base_currency = st.selectbox(
        "Выберите базовую валюту:",
        ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY"],
        index=0
    )
    
    st.markdown("---")
    st.info("📊 Источники: Frankfurter.app, ExchangeRate-API\n\n🔄 Обновление: ежедневно")
    
    if st.button("🔄 Обновить данные"):
        st.cache_data.clear()
        st.rerun()

# Загрузка данных
df_rates, update_date, api_source = fetch_currency_rates(base_currency)

if df_rates is not None:
    st.info(f"📅 Актуально на: {update_date} | Источник: {api_source}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"📊 Курсы валют относительно {base_currency}")
        df_display = df_rates.copy()
        df_display['Курс'] = df_display['Курс'].apply(lambda x: f"{x:.4f}")
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("📈 Топ-10 самых дорогих валют")
        top_10 = df_rates[df_rates['Валюта'] != base_currency].head(10)
        
        fig = plt.bar(
            top_10,
            x='Курс',
            y='Валюта',
            orientation='h',
            title=f'Топ-10 валют относительно {base_currency}',
            color='Курс',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📊 Статистика")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        st.metric("Всего валют", len(df_rates) - 1)
    
    with col4:
        max_currency = df_rates[df_rates['Валюта'] != base_currency].iloc[0]
        st.metric("Самая дорогая", max_currency['Валюта'], f"{max_currency['Курс']:.4f} {base_currency}")
    
    with col5:
        min_currency = df_rates[df_rates['Валюта'] != base_currency].iloc[-1]
        st.metric("Самая дешевая", min_currency['Валюта'], f"{min_currency['Курс']:.4f} {base_currency}")
    
    # Конвертер
    st.markdown("---")
    st.subheader("💱 Конвертер валют")
    
    col6, col7, col8 = st.columns(3)
    
    with col6:
        amount = st.number_input("Сумма:", min_value=0.0, value=100.0)
    
    with col7:
        from_currency = st.selectbox("Из валюты:", df_rates['Валюта'].tolist())
    
    with col8:
        to_currency = st.selectbox("В валюту:", df_rates['Валюта'].tolist())
    
    if from_currency != to_currency:
        from_rate = df_rates[df_rates['Валюта'] == from_currency]['Курс'].values[0]
        to_rate = df_rates[df_rates['Валюта'] == to_currency]['Курс'].values[0]
        
        if from_currency == base_currency:
            converted = amount * to_rate
        elif to_currency == base_currency:
            converted = amount / from_rate
        else:
            converted = amount * (to_rate / from_rate)
        
        st.success(f"💵 {amount:.2f} {from_currency} = {converted:.2f} {to_currency}")

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>💱 Дашборд создан с использованием Streamlit</p>",
    unsafe_allow_html=True
)
