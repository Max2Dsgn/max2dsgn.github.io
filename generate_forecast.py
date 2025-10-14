import os
import json
import datetime
import feedparser
import openai
import tempfile
import shutil

# ==============================
# 🔧 Настройки
# ==============================
openai.api_key = os.getenv("OPENAI_API_KEY")

RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.producthunt.com/feed",
    "https://rssexport.rbc.ru/rbcnews/technology/20/full.rss",
    "https://habr.com/ru/rss/all/all/",
]

KEYWORDS = [
    "tech", "technology", "startup", "innovation", "ai", "machine learning",
    "ux", "ui", "product", "design", "digital", "robot", "future", "trend",
    "технолог", "инновац", "стартап", "дизайн", "цифров", "продукт", "робот"
]

DATA_DIR = "data"
HISTORY_PATH = os.path.join(DATA_DIR, "forecasts_history.json")
MAX_HISTORY = 7  # сохраняем последние 7 записей


# ==============================
# 🧩 Безопасная загрузка JSON
# ==============================
def safe_load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Ошибка чтения {path}: {e}. Создаём новый файл.")
        return []


# ==============================
# 💾 Безопасная запись JSON
# ==============================
def safe_write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(path), encoding="utf-8") as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
    shutil.move(tmp.name, path)


# ==============================
# 📰 Сбор новостей
# ==============================
def get_recent_headlines():
    headlines = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            title = entry.title
            if any(k.lower() in title.lower() for k in KEYWORDS):
                headlines.append(title)
    return headlines[:20]


# ==============================
# 🤖 Генерация прогноза
# ==============================
def generate_forecast(news_headlines):
    if not news_headlines:
        print("⚠️ Нет свежих новостей, прогноз не создан.")
        return ""

    joined = "\n".join([f"- {h}" for h in news_headlines])

    prompt = f"""
Ты — эксперт по технологиям, продуктам и дизайну.
Используя новости (ниже), составь краткий прогноз на неделю, месяц и год:
{joined}

Сконцентрируйся на технологических и продуктовых трендах, влиянии ИИ, UX/UI-дизайне и цифровых изменениях.
Ответ на русском языке, без политики и военных тем.
"""

    try:
        response = openai.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            max_output_tokens=700,
            temperature=0.7,
        )
        forecast = response.output[0].content[0].text.strip()
        return forecast
    except Exception as e:
        print(f"❌ Ошибка при вызове OpenAI API: {e}")
        return ""


# ==============================
# 🚀 Основная логика
# ==============================
def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Загружаем старые прогнозы
    history = safe_load_json(HISTORY_PATH)

    # Сбор новостей и генерация нового прогноза
    headlines = get_recent_headlines()
    forecast = generate_forecast(headlines)

    if not forecast.strip():
        print("⚠️ Прогноз пустой, запись пропущена.")
        return

    today = datetime.date.today().isoformat()

    # Добавляем новую запись в начало
    history.insert(0, {"date": today, "forecast": forecast})
    history = history[:MAX_HISTORY]

    # Безопасно сохраняем
    safe_write_json(HISTORY_PATH, history)

    print(f"✅ Прогноз обновлён ({today}).")


if __name__ == "__main__":
    main()
