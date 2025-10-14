import openai
import feedparser
import json
import os
from datetime import datetime, date
import streamlit as st

# ==============================
# ⚙️ Конфигурация приложения
# ==============================

st.set_page_config(page_title="AI FutureCast", page_icon="🔮", layout="centered")

st.title("🔮 AI FutureCast: прогнозы для технологий и продуктового дизайна")
st.write("ИИ анализирует свежие технологические новости и формирует прогноз будущих трендов — на неделю, месяц и год.")

# RSS-источники
RSS_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Wired": "https://www.wired.com/feed/rss",
    "ProductHunt": "https://www.producthunt.com/feed",
    "VentureBeat": "https://venturebeat.com/feed/",
    "РБК Технологии": "https://rssexport.rbc.ru/rbcnews/technology/20/full.rss",
    "Хабр": "https://habr.com/ru/rss/all/all/",
}

# Ключевые слова — русские + английские
KEYWORDS = [
    # Русские
    "технолог", "стартап", "дизайн", "ux", "ui", "интерфейс",
    "искусственный интеллект", "машинное обучение", "инновац",
    "продукт", "гаджет", "разработка", "программирование", "робот",
    "тренд", "новинка", "it", "технологии", "цифров", "метавселенн",
    # Английские
    "technology", "tech", "startup", "innovation", "design", "ux", "ui",
    "interface", "product", "ai", "machine learning", "artificial intelligence",
    "app", "mobile", "software", "hardware", "gadget", "developer", "digital",
    "trend", "cloud", "data", "robot", "automation", "saas", "launch", "productivity",
    "future", "ui/ux", "user experience", "human-centered", "prototype", "creativity"
]

# Файл истории
HISTORY_FILE = "data/forecasts_history.json"
os.makedirs("data", exist_ok=True)

# ==============================
# 📰 Работа с новостями
# ==============================

def get_filtered_headlines():
    """Загружает и фильтрует новости по ключевым словам."""
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
    return headlines[:20]


# ==============================
# 🧠 Прогноз от OpenAI
# ==============================

def build_prompt(headlines):
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

Добавь в конце краткие рекомендации для дизайнеров и продуктовых специалистов.

Новости (актуально на {now}):
{joined}

Ответ дай на русском языке.
"""

def call_openai(prompt):
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


# ==============================
# 💾 Работа с историей прогнозов
# ==============================

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_forecast(forecast_text):
    history = load_history()
    today = date.today().isoformat()
    # Проверяем, не записан ли уже прогноз на сегодня
    if any(entry["date"] == today for entry in history):
        return
    entry = {"date": today, "forecast": forecast_text}
    history.insert(0, entry)
    history = history[:7]  # храним неделю
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ==============================
# 🎨 Интерфейс
# ==============================

st.divider()
st.write("🔍 Сбор данных из технологических источников...")

headlines = get_filtered_headlines()

if not headlines:
    st.error("Не удалось получить новости. Попробуй позже.")
else:
    st.success(f"Получено {len(headlines)} релевантных новостей.")
    with st.expander("Показать новости, по которым строится прогноз"):
        for h in headlines:
            st.write("•", h)

    if st.button("✨ Сгенерировать прогноз"):
        with st.spinner("ИИ анализирует тренды..."):
            prompt = build_prompt(headlines)
            forecast = call_openai(prompt)
            st.divider()
            st.subheader("📊 Прогноз")
            st.write(forecast)
            st.caption(f"Обновлено {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            save_forecast(forecast)

# ==============================
# 📜 История прогнозов
# ==============================

st.divider()
st.subheader("🕓 История прогнозов (последние 7 дней)")
history = load_history()

if history:
    for entry in history[:3]:  # показываем последние 3
        with st.expander(f"📅 {entry['date']}"):
            st.write(entry["forecast"])
else:
    st.info("История пока пуста. Сгенерируй первый прогноз!")

st.divider()
st.caption("AI FutureCast © 2025 — ежедневные технологические прогнозы для продуктовых дизайнеров и технологов.")
