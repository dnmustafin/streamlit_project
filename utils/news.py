import requests
import streamlit as st
import feedparser
from datetime import datetime

@st.cache_data(ttl=1800)
def get_crypto_news():
    """Получает последние новости о криптовалютах"""
    try:
        # RSS фиды
        feeds = [
            'https://cointelegraph.com/rss',
            'https://www.coindesk.com/arc/outboundfeeds/rss/',
        ]
        
        all_news = []
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:
                    all_news.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': entry.published if hasattr(entry, 'published') else datetime.now().strftime("%Y-%m-%d"),
                        'source': feed_url.split('/')[2]
                    })
            except:
                continue
        
        return all_news[:10]
    except:
        return [
            {'title': 'Не удалось загрузить новости', 'link': '#', 'published': '', 'source': ''}
        ]

def get_forex_news():
    """Получает новости о валютном рынке"""
    # Простая имитация - можно подключить реальный API
    return [
        {'title': 'ФРС сохраняет ключевую ставку', 'link': '#', 'importance': 'high'},
        {'title': 'ЕЦБ сигнализирует о возможном снижении ставок', 'link': '#', 'importance': 'medium'},
        {'title': 'Японская иена укрепляется на фоне интервенций', 'link': '#', 'importance': 'high'},
        {'title': 'Нефть Brent: влияние на валюты экспортеров', 'link': '#', 'importance': 'medium'},
    ]