import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
import anthropic
from tavily import TavilyClient

# ── CONFIG ──────────────────────────────────────────
ANTHROPIC_API_KEY     = os.environ["ANTHROPIC_API_KEY"]
TAVILY_API_KEY        = os.environ["TAVILY_API_KEY"]
SENDER_EMAIL          = os.environ["SENDER_EMAIL"]
SENDER_PASSWORD       = os.environ["SENDER_PASSWORD"]
READWISE_INBOX_EMAIL  = os.environ["READWISE_INBOX_EMAIL"]

TOPICS = [

    # ── TOYOTA GLOBAL ───────────────────────────────
    "Toyota Motor global strategy announcement",
    "Toyota new model launch reveal 2025 2026",
    "Toyota BEV electric vehicle platform update",
    "Toyota GR sport performance news",
    "Toyota financial results earnings",

    # ── TOYOTA SEA KEY MARKETS ───────────────────────
    "Toyota Thailand new model sales launch",
    "Toyota Indonesia new model sales launch",
    "Toyota Malaysia new model sales",
    "Toyota Vietnam Philippines automotive",
    "Toyota Hilux Fortuner Innova SEA update",
    "TMA Toyota Motor Asia announcement",

    # ── JAPANESE COMPETITORS SEA ─────────────────────
    "Honda new model launch SEA Thailand Indonesia",
    "Nissan new model SEA strategy 2025 2026",
    "Mazda new model SEA Thailand Indonesia",

    # ── CHINESE BRANDS SEA ───────────────────────────
    "BYD Thailand Indonesia Malaysia sales launch",
    "MG SAIC new model SEA Thailand",
    "Chery Omoda Jaecoo SEA launch Thailand Indonesia",
    "Geely Lynk Co SEA expansion",
    "Changan new model Southeast Asia",

    # ── GLOBAL AUTOMOTIVE MACRO ──────────────────────
    "electric vehicle EV policy regulation 2025",
    "automotive tariff trade war impact",
    "global car sales market share report",
    "battery technology EV range breakthrough",
]

# ── FETCH ────────────────────────────────────────────
def fetch_news():
    client = TavilyClient(api_key=TAVILY_API_KEY)
    all_results = []
    for topic in TOPICS:
        results = client.search(
            query=topic,
            max_results=3,
            search_depth="basic",
            include_raw_content=False
        )
        for r in results.get("results", []):
            all_results.append({
                "title": r.get("title", ""),
                "url":   r.get("url", ""),
                "body":  r.get("content", "")[:400]
            })
    return all_results

# ── SUMMARIZE ────────────────────────────────────────
def summarize(articles):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    articles_text = ""
    for i, a in enumerate(articles, 1):
        articles_text += f"{i}. {a['title']}\n{a['url']}\n{a['body']}\n\n"

    prompt = f"""
You are an automotive industry intelligence analyst.
Today is {date.today().strftime('%d %B %Y')}.

Below are raw news articles fetched from the web.
Produce a concise executive brief in clean HTML format using these exact tags:

<h3>MUST READ</h3>
For each must-read item (pick 3-5 most important):
<div class="item">
<b>Title</b> | Source<br>
<a href="URL">URL</a><br>
<i>So what:</i> 2 sentences why this matters for Toyota/SEA automotive.
</div>

<h3>HEADLINES ONLY</h3>
For remaining items:
<div class="item">
Title | Source | <a href="URL">link</a>
</div>

<h3>TREND SIGNAL</h3>
<div class="item">
<b>Theme:</b> one sentence per signal.
</div>

Rules: No markdown. No asterisks. No dashes. Only HTML tags above.
Prioritize Toyota, SEA market, BEV/EV policy, competitor moves.
Ignore PR fluff and unrelated content.

ARTICLES:
{articles_text}
"""
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# ── EMAIL ────────────────────────────────────────────
def send_email(brief_text):
    today = date.today().strftime('%d %b %Y')
    subject = f"Automotive Intel Brief — {today}"

    html_body = f"""
<html>
<head>
<style>
  body {{ font-family: Georgia, serif; max-width: 680px; margin: auto; 
         padding: 24px; color: #222; background: #fff; }}
  h2 {{ border-bottom: 2px solid #c0392b; padding-bottom: 8px; }}
  h3 {{ color: #c0392b; margin-top: 28px; margin-bottom: 8px; }}
  .item {{ margin-bottom: 16px; line-height: 1.7; }}
  a {{ color: #c0392b; }}
  i {{ color: #555; }}
</style>
</head>
<body>
<h2>Automotive Intel Brief<br>
<span style="font-size:14px;color:#666;">{today}</span></h2>
{brief_text}
<hr style="margin-top:32px;border:none;border-top:1px solid #ddd;">
<p style="font-size:12px;color:#999;">Voyage Agent · daily brief</p>
</body></html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = READWISE_INBOX_EMAIL
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, READWISE_INBOX_EMAIL, msg.as_string())

    print(f"Brief sent to {READWISE_INBOX_EMAIL}")

# ── MAIN ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Fetching news...")
    articles = fetch_news()
    print(f"Fetched {len(articles)} articles. Summarizing...")
    brief = summarize(articles)
    print(brief)
    print("Sending email...")
    send_email(brief)
    print("Done.")
