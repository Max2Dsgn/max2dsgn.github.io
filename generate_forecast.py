import os, feedparser, json, datetime, openai

openai.api_key = os.getenv("OPENAI_API_KEY")

RSS = [
  "https://techcrunch.com/feed/",
  "https://www.theverge.com/rss/index.xml",
  "https://www.wired.com/feed/rss",
  "https://www.producthunt.com/feed",
  "https://rssexport.rbc.ru/rbcnews/technology/20/full.rss",
  "https://habr.com/ru/rss/all/all/",
]

KEYWORDS = ["tech", "technology", "startup", "innovation", "design", "ai", "machine learning",
            "ux", "ui", "продукт", "технолог", "инновац", "дизайн", "цифров", "робот"]

headlines = []
for url in RSS:
    feed = feedparser.parse(url)
    for entry in feed.entries:
        title = entry.title
        if any(k.lower() in title.lower() for k in KEYWORDS):
            headlines.append(title)
headlines = headlines[:20]

joined = "\n".join([f"- {h}" for h in headlines])
prompt = f"""Ты — эксперт в технологиях и дизайне. Используя новости:
{joined}
Дай краткий прогноз на неделю, месяц и год для технологических и продуктовых трендов (на русском языке)."""

response = openai.completions.create(
    model="gpt-4o-mini",
    prompt=prompt,
    max_tokens=700,
    temperature=0.7,
)
forecast = response.choices[0].text.strip()

os.makedirs("data", exist_ok=True)
history_path = "data/forecasts_history.json"
today = datetime.date.today().isoformat()
if os.path.exists(history_path):
    with open(history_path, "r") as f:
        history = json.load(f)
else:
    history = []
history.insert(0, {"date": today, "forecast": forecast})
history = history[:7]
with open(history_path, "w") as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print("✅ Forecast updated for", today)
