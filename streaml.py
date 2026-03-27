import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Импортируем модули
from utils.api import fetch_currency_rates, get_historical_rates
from utils.charts import (
    create_top_currencies_chart,
    create_historical_chart,
    create_world_map,
    create_comparison_chart
)
from utils.ml import predict_rate, detect_anomaly
from utils.export import export_to_excel, export_to_csv, export_to_json
from utils.alerts import check_alerts
from utils.news import get_crypto_news, get_forex_news

# Настройка страницы
st.set_page_config(
    page_title="Финансовый дашборд | Курсы валют",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация session state
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
if 'historical_cache' not in st.session_state:
    st.session_state.historical_cache = {}

# CSS для темной темы
def apply_theme():
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
        }
        .stMarkdown, .stText, .stNumberInput, .stSelectbox {
            color: #ffffff;
        }
        .stMetric {
            background-color: #1e1e2e;
            border-radius: 10px;
            padding: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

# Функция для ленивой загрузки исторических данных (с кэшированием)
@st.cache_data(ttl=3600)
def load_historical_data(currency, base_currency):
    """Загружает исторические данные с кэшированием"""
    return get_historical_rates(currency, base_currency, days=30)

def get_historical_with_cache(currency, base_currency):
    """Получает исторические данные из кэша session_state"""
    cache_key = f"{currency}_{base_currency}"
    if cache_key not in st.session_state.historical_cache:
        with st.spinner(f"📊 Загрузка истории для {currency}..."):
            st.session_state.historical_cache[cache_key] = load_historical_data(currency, base_currency)
    return st.session_state.historical_cache[cache_key]

# Заголовок
st.title("💱 Финансовый дашборд")
st.markdown("Актуальные курсы валют, прогнозы и аналитика")

# Сайдбар
with st.sidebar:
    st.header("⚙️ Настройки")
    
    # Выбор базовой валюты
    base_currency = st.selectbox(
        "💰 Базовая валюта:",
        ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "RUB"],
        index=0
    )
    
    st.markdown("---")
    
    # Настройки отображения
    st.subheader("🎨 Внешний вид")
    theme = st.selectbox("Тема:", ['light', 'dark'], index=0 if st.session_state.theme == 'light' else 1)
    if theme != st.session_state.theme:
        st.session_state.theme = theme
        st.rerun()
    
    auto_refresh = st.checkbox("🔄 Автообновление (30 сек)")
    show_news = st.checkbox("📰 Показывать новости", value=True)
    
    st.markdown("---")
    
    # Кнопка обновления
    if st.button("🔄 Обновить данные"):
        st.cache_data.clear()
        st.session_state.historical_cache = {}
        st.rerun()
    
    st.markdown("---")
    st.info("📊 Источники: Frankfurter.app, ExchangeRate-API\n\n🤖 Прогнозы: ML (Linear + Polynomial Regression)")

# Применяем тему
apply_theme()

# Получаем данные
with st.spinner("Загрузка курсов валют..."):
    df_rates, update_date, api_source = fetch_currency_rates(base_currency)

if df_rates is None:
    st.error("❌ Не удалось загрузить данные. Проверьте подключение к интернету.")
    st.stop()

# Основная информация
st.success(f"✅ Данные актуальны на: **{update_date}** | Источник: {api_source}")

# Автообновление
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Получаем исторические данные только для топ-3 валют (для алертов)
historical_for_alerts = {}
top_currencies_for_alerts = df_rates[df_rates['Валюта'] != base_currency].head(3)['Валюта'].tolist()
for currency in top_currencies_for_alerts:
    historical_for_alerts[currency] = get_historical_with_cache(currency, base_currency)

# Проверяем алерты
alerts = check_alerts(df_rates, historical_for_alerts)
if alerts:
    with st.container():
        st.warning("⚠️ **Внимание! Важные изменения:**")
        for alert in alerts[:5]:  # Показываем не более 5 алертов
            st.warning(alert['message'])

# Основные метрики
st.markdown("---")
st.subheader("📊 Ключевые показатели")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Всего валют", len(df_rates) - 1)

with col2:
    max_currency = df_rates[df_rates['Валюта'] != base_currency].iloc[-1]
    st.metric("Самая дорогая", f"{max_currency['Валюта']}", f"{max_currency['Курс']:.4f} {base_currency}")

with col3:
    min_currency = df_rates[df_rates['Валюта'] != base_currency].iloc[0]
    st.metric("Самая дешевая", f"{min_currency['Валюта']}", f"{min_currency['Курс']:.4f} {base_currency}")

with col4:
    top10 = df_rates[df_rates['Валюта'] != base_currency].head(10)
    volatility = top10['Курс'].std()
    st.metric("Волатильность (σ)", f"{volatility:.4f}", help="Стандартное отклонение топ-10 валют")

# Две основные колонки
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Топ-10 валют")
    fig = create_top_currencies_chart(df_rates, base_currency, n=10)
    st.plotly_chart(fig, width="stretch")

with col_right:
    st.subheader("🗺️ Карта мира")
    world_map = create_world_map(df_rates)
    if world_map:
        st.plotly_chart(world_map, width="stretch")
    else:
        st.info("Карта мира доступна для основных валют")

# Исторические графики
st.markdown("---")
st.subheader("📉 Исторические данные и прогнозы")

col_hist, col_pred = st.columns(2)

with col_hist:
    hist_currency = st.selectbox(
        "Выберите валюту для графика:",
        df_rates[df_rates['Валюта'] != base_currency]['Валюта'].tolist(),
        key="hist_selector"
    )
    
    if hist_currency:
        hist_data = get_historical_with_cache(hist_currency, base_currency)
        hist_fig = create_historical_chart(hist_data, hist_currency, base_currency)
        if hist_fig:
            st.plotly_chart(hist_fig, width="stretch")
            
            # Проверка аномалий
            if hist_data is not None and len(hist_data) > 0:
                current_rate = df_rates[df_rates['Валюта'] == hist_currency]['Курс'].values[0]
                is_anomaly = detect_anomaly(hist_data, current_rate)
                if is_anomaly:
                    st.error(f"🚨 Аномалия: текущий курс {hist_currency} значительно отличается от исторических значений!")
        else:
            st.info("Недостаточно исторических данных для построения графика")

with col_pred:
    pred_currency = st.selectbox(
        "Выберите валюту для прогноза:",
        df_rates[df_rates['Валюта'] != base_currency]['Валюта'].tolist(),
        key="pred_selector"
    )
    
    if pred_currency:
        hist_data = get_historical_with_cache(pred_currency, base_currency)
        if hist_data is not None and len(hist_data) >= 7:
            with st.spinner("🔄 Вычисление прогноза..."):
                prediction, confidence = predict_rate(hist_data, days_ahead=7)
            
            if prediction is not None:
                st.write(f"**📈 Прогноз для {pred_currency} на 7 дней вперед:**")
                
                # Создаем график с прогнозом
                fig = go.Figure()
                
                # Исторические данные
                fig.add_trace(go.Scatter(
                    x=hist_data['date'],
                    y=hist_data['rate'],
                    mode='lines+markers',
                    name='Исторические данные',
                    line=dict(color='blue')
                ))
                
                # Прогноз
                future_dates = [(datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(7)]
                fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=prediction,
                    mode='lines+markers',
                    name='Прогноз',
                    line=dict(color='red', dash='dash')
                ))
                
                # Доверительный интервал
                if confidence:
                    lower, upper = confidence
                    fig.add_trace(go.Scatter(
                        x=future_dates + future_dates[::-1],
                        y=list(upper) + list(lower)[::-1],
                        fill='toself',
                        fillcolor='rgba(255,0,0,0.2)',
                        line=dict(color='rgba(255,0,0,0)'),
                        name='Доверительный интервал (95%)'
                    ))
                
                fig.update_layout(
                    title=f'Прогноз курса {pred_currency} к {base_currency}',
                    xaxis_title="Дата",
                    yaxis_title="Курс",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, width="stretch")
                
                # Показываем прогнозные значения в таблице
                pred_df = pd.DataFrame({
                    'Дата': future_dates,
                    'Прогнозный курс': [f"{x:.4f}" for x in prediction]
                })
                st.dataframe(pred_df, width="stretch", hide_index=True)
            else:
                st.warning("Не удалось построить прогноз")
        else:
            st.warning(f"Недостаточно исторических данных для прогноза (нужно минимум 7 дней, есть {len(hist_data) if hist_data is not None else 0})")

# Сравнение валют
st.markdown("---")
st.subheader("⚖️ Сравнение валют")

col_comp1, col_comp2 = st.columns(2)

with col_comp1:
    currency1 = st.selectbox(
        "Валюта 1:",
        df_rates['Валюта'].tolist(),
        key="comp1"
    )

with col_comp2:
    currency2 = st.selectbox(
        "Валюта 2:",
        df_rates['Валюта'].tolist(),
        key="comp2"
    )

if currency1 and currency2 and currency1 != currency2:
    comp_fig = create_comparison_chart(df_rates, currency1, currency2)
    st.plotly_chart(comp_fig, width="stretch")

# Конвертер валют
st.markdown("---")
st.subheader("💱 Конвертер валют")

conv_col1, conv_col2, conv_col3 = st.columns(3)

with conv_col1:
    amount = st.number_input("Сумма:", min_value=0.0, value=100.0, step=10.0)

with conv_col2:
    from_currency = st.selectbox("Из валюты:", df_rates['Валюта'].tolist(), key="from")

with conv_col3:
    to_currency = st.selectbox("В валюту:", df_rates['Валюта'].tolist(), key="to")

if from_currency != to_currency:
    from_rate = df_rates[df_rates['Валюта'] == from_currency]['Курс'].values[0]
    to_rate = df_rates[df_rates['Валюта'] == to_currency]['Курс'].values[0]
    
    if from_currency == base_currency:
        converted = amount * to_rate
    elif to_currency == base_currency:
        converted = amount / from_rate
    else:
        converted = amount * (to_rate / from_rate)
    
    st.success(f"💵 **{amount:.2f} {from_currency} = {converted:.2f} {to_currency}**")

# Полная таблица курсов
with st.expander("📋 Полная таблица курсов валют", expanded=False):
    df_display = df_rates.copy()
    df_display['Курс'] = df_display['Курс'].apply(lambda x: f"{x:.4f}")
    st.dataframe(df_display, width="stretch", hide_index=True)

# Экспорт данных
with st.expander("📥 Экспорт данных", expanded=False):
    export_format = st.selectbox("Формат файла:", ["Excel", "CSV", "JSON"])
    
    if export_format == "Excel":
        file_data = export_to_excel(df_rates)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    elif export_format == "CSV":
        file_data = export_to_csv(df_rates)
        mime = "text/csv"
        ext = "csv"
    else:
        file_data = export_to_json(df_rates)
        mime = "application/json"
        ext = "json"
    
    st.download_button(
        label=f"📥 Скачать {export_format}",
        data=file_data,
        file_name=f"currency_rates_{datetime.now().strftime('%Y%m%d')}.{ext}",
        mime=mime
    )

# Новости
if show_news:
    st.markdown("---")
    st.subheader("📰 Новости рынка")
    
    news_col1, news_col2 = st.columns(2)
    
    with news_col1:
        st.write("**💰 Forex новости:**")
        forex_news = get_forex_news()
        for news in forex_news:
            importance_icon = "🔴" if news.get('importance') == 'high' else "🟡"
            st.markdown(f"{importance_icon} [{news['title']}]({news['link']})")
    
    with news_col2:
        st.write("**🪙 Крипто новости:**")
        crypto_news = get_crypto_news()
        for news in crypto_news[:5]:
            st.markdown(f"📰 [{news['title'][:80]}...]({news['link']})")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>💱 Финансовый дашборд | Технологии: Python, Streamlit, Pandas, Plotly, Scikit-learn</p>
        <p>📊 Данные: Frankfurter.app, ExchangeRate-API | 🤖 Прогнозы: ML (Linear + Polynomial Regression)</p>
        <p>🔄 Автообновление каждые 30 секунд (опционально)</p>
    </div>
    """,
    unsafe_allow_html=True
)