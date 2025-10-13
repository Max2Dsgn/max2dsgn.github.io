import streamlit as st
import feedparser
import openai
import time
import json
from datetime import datetime

st.set_page_config(page_title="Прогноз Будущего 🔮", page_icon="🔮", layout="centered")
st.title("Прогноз Будущего 🔮")
st.write("Короткие прогнозы на неделю, месяц и год — сгенерированные ИИ на основе свежих мировых и российских новостей. \
Прототип: обновление вручную. Для продакшен-автоматизации — используйте cron/GitHub Actions.")

# --- Settings ---
RSS_FEEDS = {
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Reuters World": "http://feeds.reuters.com/Reuters/worldNews",
    "TASS (ru)": "https://tass.com/rss/v2.xml",
    "RBC (ru)": "https://www.rbc.ru/rbcnews.rss",
    "RIA Novosti (ru)": "https://ria.ru/export/rss2/index.xml"
}
MAX_HEADLINES = 12
CONTEXT_TRIM_CHARS = 3000

# --- OpenAI key ---
if "OPENAI_API_KEY" not in st.secrets:
    st.warning("Не найден OPENAI_API_KEY в секретах Streamlit. Добавьте его в Secrets.")
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")

# --- Utilities ---
def fetch_headlines(feeds, max_total=12):
    headlines = []
    for name, url in feeds.items():
        try:
            d = feedparser.parse(url)
            for entry in d.entries[:3]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                headlines.append(f"{name}: {title} — {summary}")
                if len(headlines) >= max_total:
                    return headlines
        except Exception as e:
            # ignore feed errors
            continue
    return headlines

def build_prompt(headlines):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    joined = "\n".join([f"- {h}" for h in headlines])
    if len(joined) > CONTEXT_TRIM_CHARS:
        joined = joined[:CONTEXT_TRIM_CHARS] + "\n... (truncated)"
    prompt = f"""
Ты — экспертный аналитик. На основе приведённых ниже свежих новостей (смешанные мировые и российские источники)
сформулируй лаконичные прогнозы в вежливой профессиональной форме на трёх горизонтах:
1) На неделю — ключевые ожидаемые изменения и что стоит отслеживать.
2) На месяц — вероятные тренды и возможные риски.
3) На год — направление развития и крупные сдвиги, которые могут произойти.

Ограничься примерно 3–5 предложениями на каждый горизонт. Выдели вероятность (низкая/средняя/высокая) у каждого пункта в скобках.
Добавь в конце 1–2 кратких рекомендаций для продуктового дизайнера.

Контекст (новости собраны по %s):
%s

Ответ дай на русском языке.
""" % (now, joined)
    return prompt

def call_openai(prompt, model="gpt-4o-mini", temperature=0.7, max_tokens=600):
    if not openai.api_key:
        return "Ошибка: отсутствует API-ключ OpenAI. Установите OPENAI_API_KEY в секретах."
    try:
        response = openai.completions.create(
            model=model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Ошибка при вызове OpenAI API: {e}"

# --- UI ---
st.sidebar.header("Настройки (прототип)")
st.sidebar.write("Можно менять число заголовков и модель (если у вас доступ)")
max_items = st.sidebar.slider("Макс. заголовков из RSS", 5, 30, MAX_HEADLINES)
model = st.sidebar.text_input("Модель (OpenAI)", value="gpt-4o-mini")
temp = st.sidebar.slider("Температура ИИ", 0.0, 1.0, 0.7)

st.markdown("---")
st.subheader("Источник новостей")
st.write("Собираются топ-заголовки из выбранных RSS-лент (мировые + российские).")

col1, col2 = st.columns([3,1])
with col1:
    if st.button("Обновить прогноз (ИИ)"):
        with st.spinner("Собираем новости..."):
            headlines = fetch_headlines(RSS_FEEDS, max_total=max_items)
            if not headlines:
                st.error("Не удалось получить заголовки из RSS. Проверьте доступ к сети или RSS-ленты.")
            else:
                st.info(f"Собрано {len(headlines)} заголовков. Формируем промпт и обращаемся к OpenAI...")
                prompt = build_prompt(headlines)
                forecast = call_openai(prompt, model=model, temperature=float(temp))
                # save to local file (append)
                record = {
                    "time": datetime.utcnow().isoformat(),
                    "model": model,
                    "temperature": temp,
                    "headlines": headlines,
                    "forecast": forecast
                }
                try:
                    # append to history file
                    history_path = "data/forecasts_history.json"
                    try:
                        with open(history_path, "r", encoding="utf-8") as f:
                            hist = json.load(f)
                    except:
                        hist = []
                    hist.insert(0, record)
                    with open(history_path, "w", encoding='utf-8') as f:
                        json.dump(hist[:200], f, ensure_ascii=False, indent=2)
                except Exception as e:
                    st.error(f"Не удалось сохранить историю: {e}")
                st.subheader("🔮 Сгенерированный прогноз")
                st.markdown(f"```\n{forecast}\n```")
    else:
        st.write("Нажмите кнопку **Обновить прогноз (ИИ)** чтобы получить свежий прогноз.")

with col2:
    st.write("История (последние прогнозы)")
    try:
        with open("data/forecasts_history.json", "r", encoding='utf-8') as f:
            hist = json.load(f)
        for r in hist[:5]:
            t = r.get("time","?")
            st.write(f"- {t} — {r.get('model','?')}")
    except Exception:
        st.write("История пуста.")

st.markdown("---")
st.subheader("Как это работает (коротко)")
st.write("""
1. Сбор новостей из RSS (несколько источников).  
2. Конструирование промпта и отправка в OpenAI.  
3. Публикация краткого прогноза и сохранение в истории.  
Это прототип — не даёт гарантий и не проверяет точность автоматически.
""")

st.caption("Прототип создан для демонстрации идеи. Не используйте прогнозы как единственный источник решений.")
