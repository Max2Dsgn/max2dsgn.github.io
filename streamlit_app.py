import openai
import feedparser
from datetime import datetime
import streamlit as st

# Настройки страницы
st.set_page_config(page_title="AI FutureCast", page_icon="🔮", layout="centered")

st.title("🔮 AI FutureCast: прогнозы для технологий и продуктового дизайна")
st.write("Каждый день — новый прогноз технологических и дизайнерских трендов, созданный ИИ на основе актуальных мировых новостей.")

# --- Конфигурация ---
# RSS-источники с фокусом на технологии и инновации
RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Wired": "https://www.wired.com/feed/rss",
    "ProductHunt": "https://www.producthunt.com/feed",
    "VentureBeat": "https://venturebeat.com/feed/",
    "РБК Технологии": "https://rssexport.rbc.ru/rbcnews/technology/20/full.rss",
    "Хабр": "https://habr.com/ru/rss/all/all/",
}

# Ключевые слова для фильтрации релевантных новостей
KEYWORDS = [
    "технолог", "стартап", "дизайн", "UX", "UI", "интерфейс",
    "искусственный интеллект", "AI", "машинное обучение", "инновац",
    "продукт", "гаджет", "разработка", "программирование", "робот",
    "тренд", "новинка", "IT", "технологии"
]

# --- Функции ---

def get_filtered_headlines():
    """Получает и фильтрует новости из RSS по ключевым словам."""
    headlines = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    headlines.append(f"{title} ({source})")
        except Exception as e:
            st.warning(f"Ошибка при загрузке {source}: {e}")
    return headlines[:20]  # ограничим до 20 заголовков

def build_prompt(headlines):
    """Создает контекстный промпт для модели."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    joined = "\n".join([f"- {h}" for h in headlines])
    if len(joined) > 2000:
        joined = joined[:2000] + "\n... (truncated)"
    return f"""
Ты — эксперт в области технологий и продуктового дизайна.
Используй приведённые ниже свежие новости (мировые и российские источники)
и создай прогнозы в технологическом и дизайнерском контексте.

Формат ответа:
1️⃣ Прогноз на неделю — краткосрочные технологические и дизайнерские тренды, новые идеи и тенденции.
2️⃣ Прогноз на месяц — куда движутся технологии, продукты и дизайн-индустрия.
3️⃣ Прогноз на год — крупные изменения, тренды и инновации, которые могут повлиять на продуктовых дизайнеров и технологические компании.

Дай также короткие рекомендации для дизайнеров и продуктовых специалистов, чтобы они могли адаптироваться к этим изменениям.

Новости (актуально на {now}):
{joined}

Ответ дай на русском языке.
"""

def call_openai(prompt):
    """Отправляет запрос в OpenAI API и возвращает ответ."""
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    try:
        response = openai.completions.create(
            model="gpt-4o-mini",
            prompt=prompt,
            max_tokens=800,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Ошибка при вызове OpenAI API: {e}"

# --- Интерфейс приложения ---

st.divider()
st.write("🔍 Сбор данных из технологических новостных источников...")

headlines = get_filtered_headlines()

if not headlines:
    st.error("Не удалось получить релевантные новости. Попробуй позже.")
else:
    st.success(f"Получено {len(headlines)} новостей.")
    with st.expander("Показать новости, по которым строится прогноз"):
        for h in headlines:
            st.write("•", h)

    if st.button("✨ Сгенерировать прогноз"):
        with st.spinner("ИИ анализирует тренды и формирует прогноз..."):
            prompt = build_prompt(headlines)
            forecast = call_openai(prompt)
            st.divider()
            st.subheader("📊 Прогноз")
            st.write(forecast)
            st.caption(f"Обновлено {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.divider()
st.caption("AI FutureCast © 2025 — прогнозы для продуктовых дизайнеров и технологов.")
