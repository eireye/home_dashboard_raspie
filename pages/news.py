import streamlit as st
from streamlit_autorefresh import st_autorefresh
import feedparser
from datetime import datetime
import pytz

# RSS feeds - free, no API key required
NEWS_FEEDS = {
    'nrk': 'https://www.nrk.no/toppsaker.rss',
    'nrk_sport': 'https://www.nrk.no/sport/toppsaker.rss',
    'bbc_world': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    'bbc_tech': 'http://feeds.bbci.co.uk/news/technology/rss.xml',
}

@st.cache_data(ttl=600)
def get_news(feed_url):
    """Henter nyheter fra RSS feed - cached i 10 minutter"""
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        for entry in feed.entries[:10]:
            articles.append({
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', '')[:200] if entry.get('summary') else ''
            })
        return articles
    except Exception:
        return []

def clean_summary(text):
    """Clean HTML and truncate summary"""
    import re
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Truncate to ~100 chars
    if len(clean) > 100:
        clean = clean[:100].rsplit(' ', 1)[0] + "..."
    return clean

def show():
    st_autorefresh(interval=600000, key="news_refresh")

    # Two columns: Norway and World
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🇳🇴 Norge**")
        nrk_news = get_news(NEWS_FEEDS['nrk'])

        if nrk_news:
            for article in nrk_news[:3]:
                st.markdown(f"**{article['title']}**")
                if article['summary']:
                    st.caption(clean_summary(article['summary']))
                st.markdown("---")
        else:
            st.caption("Kunne ikke laste")

    with col2:
        st.markdown("**🌍 Verden**")
        bbc_news = get_news(NEWS_FEEDS['bbc_world'])

        if bbc_news:
            for article in bbc_news[:3]:
                st.markdown(f"**{article['title']}**")
                if article['summary']:
                    st.caption(clean_summary(article['summary']))
                st.markdown("---")
        else:
            st.caption("Kunne ikke laste")

def get_top_headlines(count=2):
    """Get top headlines for home page - Norway and World with summaries"""
    headlines = []

    # Norwegian news
    nrk = get_news(NEWS_FEEDS['nrk'])
    if nrk:
        for article in nrk[:count]:
            headlines.append({
                'title': article['title'],
                'summary': clean_summary(article['summary']) if article['summary'] else '',
                'source': '🇳🇴'
            })

    # World news
    bbc = get_news(NEWS_FEEDS['bbc_world'])
    if bbc:
        for article in bbc[:count]:
            headlines.append({
                'title': article['title'],
                'summary': clean_summary(article['summary']) if article['summary'] else '',
                'source': '🌍'
            })

    return headlines
