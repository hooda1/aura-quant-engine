import os
import re
import json
import time
import datetime
import requests
from xml.sax.saxutils import escape
from playwright.sync_api import sync_playwright

BASE_URL   = "https://hooda1.github.io/aura-quant-engine"
STATE_FILE = "pipeline/state.json"
ASSETS_DIR = "assets"
GUIDES_DIR = "guides"

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(GUIDES_DIR, exist_ok=True)

CAMPAIGNS = [
    {
        "id": "AURA_VAULT_ZERO_KNOWLEDGE",
        "theme": "LIGHT",
        "badge": "INVENTION // ZERO-KNOWLEDGE PATTERN VAULT",
        "sub_badge": "AES-256-GCM • OFFLINE PWA",
        "headline": "Why Cloud Vaults Leak — And How Our <span style='color:#0284c7;'>52-Billion Pattern Vault</span> Encrypts Offline.",
        "before_title": "OLD CLOUD VAULTS",
        "before": [
            "Uploads private keys & IDs to third-party servers.",
            "Shows 'Wrong Password' screens that expose vault existence.",
            "Forces $5-$15/mo recurring cloud subscriptions."
        ],
        "after_title": "AURA PATTERN VAULT ($0 CLOUD)",
        "after": [
            "310,000 PBKDF2-SHA256 rounds + AES-256-GCM in device RAM.",
            "Plausible deniability: decoy pattern opens harmless files.",
            "1-tap cryptographic shredder on iOS & Android offline."
        ],
        "term": [
            "$ aura-vault --derive-key --pbkdf2-rounds=310000",
            "OK: Derived 256-bit ephemeral key inside volatile memory",
            "OK: 0 bytes transmitted to cloud | Decoy matrix armed"
        ],
        "stats": [("Key Space", "52B+"), ("Cloud Leaks", "0 Bytes"), ("Monthly Fee", "$0")],
        "title": "How to Store Crypto Seed Phrases & Sensitive IDs Offline With Plausible Deniability",
        "slug": "offline-seed-phrase-plausible-deniability-vault",
        "labels": ["CyberSecurity", "ZeroKnowledge", "DataPrivacy", "AES256", "BoldFrameAI"],
        "target_url": f"{BASE_URL}/vault/",
        "story": (
            "Most 'encrypted' mobile vaults fail the moment someone forces you to unlock your phone.\n\n"
            "Why? Because a standard password box confirms the vault exists—and most apps sync encrypted blobs to a cloud database you don't control.\n\n"
            "At BoldFrame AI Studio, we engineered the AURA Zero-Knowledge Pattern Vault around three strict rules:\n\n"
            "1. Zero Servers: Keys are derived strictly on-device via 310,000 PBKDF2-SHA256 rounds and AES-256-GCM.\n"
            "2. Plausible Deniability: Draw Pattern A to reveal harmless decoy notes. Draw Pattern B to decrypt your actual seed phrases and IDs.\n"
            "3. 1-Tap Cryptographic Shredder: Wipes ciphertext from IndexedDB instantly with zero cloud trace.\n\n"
            "Would you trust a cloud password manager with your 24-word seed phrase, or do you keep everything strictly offline?\n\n"
            "#CyberSecurity #Privacy #ZeroKnowledge #BuildInPublic #BoldFrameAI"
        )
    },
    {
        "id": "AURA_QUANT_COMMISSION_MATH",
        "theme": "DARK",
        "badge": "INVENTION // AURA TITANIUM QUANT ENGINE",
        "sub_badge": "XAUUSD & BTCUSD • CLOSED-CANDLE",
        "headline": "Why 80% Win-Rate Gold Backtests Fail Live: <span style='color:#facc15;'>Broker Fee Drag & Repainting.</span>",
        "before_title": "RETAIL BACKTESTS",
        "before": [
            "Ignores -$7 to -$35/lot spread + commission drag.",
            "Uses repainting intra-bar indicators that vanish live.",
            "Zero real-time basis sync against broker feeds."
        ],
        "after_title": "AURA QUANT TERMINAL",
        "after": [
            "Models exact lot commission & slippage across 100 trades.",
            "Locks signals strictly after candle close (0% repaint).",
            "Runs deterministically in-browser at $0 server cost."
        ],
        "term": [
            "$ aura-quant --audit XAUUSD --lots=0.10 --trades=100",
            "OK: Net-of-fee expectancy verified after spread drag",
            "OK: 0 repainted entries | Closed-candle state locked"
        ],
        "stats": [("Repainting", "0%"), ("Audit Depth", "100 Trades"), ("Server Cost", "$0/Mo")],
        "title": "Why 80% Win-Rate XAUUSD & BTCUSD Backtests Fail Live: Commission Drag Math",
        "slug": "xauusd-btcusd-commission-drag-closed-candle-audit",
        "labels": ["QuantitativeFinance", "AlgorithmicTrading", "XAUUSD", "BTCUSD", "BoldFrameAI"],
        "target_url": f"{BASE_URL}/",
        "story": (
            "A 1-minute Gold scalping strategy that shows an 80% win rate in backtesting can still blow up a live account in two weeks.\n\n"
            "Two silent killers rarely show up in default chart previews:\n\n"
            "1. Intra-Bar Repainting: Arrows that flash mid-candle and disappear before the close make historical charts look flawless while causing live whipsaws.\n"
            "2. Fee & Spread Drag: Take 100 fast trades on XAUUSD and commission + spread silently eats a massive chunk of gross profit.\n\n"
            "We built the AURA Titanium Quant Engine to lock every setup strictly on candle close and deduct real lot-sized broker friction across every audited trade.\n\n"
            "What is the biggest gap you have noticed between TradingView backtests and live broker fills?\n\n"
            "#AlgorithmicTrading #XAUUSD #QuantFinance #TradingSystems #BoldFrameAI"
        )
    },
    {
        "id": "BOLDFRAME_CLOUD_AEO_PIPELINE",
        "theme": "LIGHT",
        "badge": "INVENTION // AUTONOMOUS AEO + API ENGINE",
        "sub_badge": "ZERO-VPS • GITHUB ACTIONS",
        "headline": "Stop Paying $500/Mo for Automation Tools: <span style='color:#0284c7;'>Direct API Pipelines</span> Beat Fragile Bots.",
        "before_title": "BROWSER-CLICKING BOTS",
        "before": [
            "Breaks every week on 'Verify it's you' & login loops.",
            "Eats tablet/VPS RAM running headless Chrome 24/7.",
            "Locks profiles and drops scheduled slots silently."
        ],
        "after_title": "DIRECT API + CLOUD CRON",
        "after": [
            "Runs on GitHub Actions cloud runners at $0/month.",
            "Permanent OAuth tokens for Blogger, X, LinkedIn & Reddit.",
            "Publishes AEO guides + RSS + Telegram proofs automatically."
        ],
        "term": [
            "$ gh workflow run autonomous_publisher.yml",
            "OK: Rendered 1200x630 & 1200x1500 visuals in 3.2s",
            "OK: Dispatched via Direct APIs | Telegram receipt sent"
        ],
        "stats": [("Hosting Cost", "$0/Mo"), ("Login Loops", "Zero"), ("Uptime", "99.9%")],
        "title": "Why Direct API Cloud Pipelines Beat Headless Browser Automation for Multi-Platform Publishing",
        "slug": "direct-api-github-actions-vs-headless-browser-bots",
        "labels": ["AIAutomation", "GitHubActions", "AEO", "GrowthEngineering", "BoldFrameAI"],
        "target_url": f"{BASE_URL}/guides/",
        "story": (
            "If your automation pipeline relies on clicking buttons inside a headless browser, you don't have an automation—you have a full-time babysitting job.\n\n"
            "Every time a platform updates a CSS class, triggers a 'Verify it's you' prompt, or locks a Chromium profile, the whole stack goes silent.\n\n"
            "At BoldFrame AI Studio, we moved our publishing and AEO guide engine to stateless cloud runners + direct REST APIs:\n\n"
            "1. Zero Cookie Decay: Permanent OAuth tokens stored in encrypted repository secrets.\n"
            "2. Zero Local Hardware Dependency: Scheduled cloud cron fires on time even if our devices are powered off.\n"
            "3. Instant Observability: Every run renders platform-specific visuals and sends live published URLs directly to Telegram.\n\n"
            "Are you still running browser-scraping bots, or have you moved your workflows to direct APIs?\n\n"
            "#Automation #SoftwareEngineering #AIAgents #BuildInPublic #BoldFrameAI"
        )
    }
]


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_idx": -1, "reddit_last_date": "", "seo_last_date": "", "published_guides": []}


def save_state(st):
    with open(STATE_FILE, "w") as f:
        json.dump(st, f, indent=2)


def refine_story_with_free_llm(campaign: dict) -> str:
    """Optionally generates a fresh hook variation via Gemini or OpenRouter if secret is set."""
    prompt = (
        f"Rewrite this founder storytelling post for LinkedIn/Blogger so it feels fresh and original today, "
        f"keeping the exact same technical facts, 150-210 words, crisp line breaks, and 5 hashtags at the end. "
        f"Do not add any links.\n\nOriginal:\n{campaign['story']}"
    )
    gem_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gem_key:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gem_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30
            )
            if r.ok:
                txt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if len(txt) > 120:
                    return txt
        except Exception as e:
            print("Gemini refine skipped:", e)

    or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if or_key:
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                json={"model": "deepseek/deepseek-chat:free", "messages": [{"role": "user", "content": prompt}]},
                timeout=30
            )
            if r.ok:
                txt = r.json()["choices"][0]["message"]["content"].strip()
                if len(txt) > 120:
                    return txt
        except Exception as e:
            print("OpenRouter refine skipped:", e)

    return campaign["story"]


def render_high_ctr_images(c: dict, tag: str):
    is_light = c["theme"] == "LIGHT"
    bg = "linear-gradient(180deg,#f8fafc 0%,#e2e8f0 100%)" if is_light else "radial-gradient(circle at 50% 0%,#1e293b 0%,#070b14 80%)"
    fg = "#0f172a" if is_light else "#ffffff"
    sub = "#334155" if is_light else "#cbd5e1"
    card_bg = "#ffffff" if is_light else "#0f172a"
    border = "#cbd5e1" if is_light else "rgba(250,204,21,0.45)"

    paths = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for key, (w, h) in [("wide", (1200, 630)), ("tall", (1200, 1500))]:
            is_tall = h > w
            middle = ""
            if is_tall:
                b_items = "".join(f"<div style='font-size:21px;line-height:1.45;font-weight:600;margin-bottom:10px;'>• {x}</div>" for x in c["before"])
                a_items = "".join(f"<div style='font-size:21px;line-height:1.45;font-weight:700;margin-bottom:10px;'>✓ {x}</div>" for x in c["after"])
                t_items = "".join(f"<div style='font-size:19px;line-height:1.6;'>{x}</div>" for x in c["term"])
                middle = f"""
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:20px 0;">
                  <div style="background:rgba(244,63,94,0.08);border:2px solid #f43f5e;border-radius:18px;padding:24px;">
                    <div style="color:#e11d48;font-weight:900;font-size:20px;margin-bottom:12px;">✕ {c['before_title']}</div>{b_items}
                  </div>
                  <div style="background:rgba(16,185,129,0.10);border:2px solid #10b981;border-radius:18px;padding:24px;">
                    <div style="color:#059669;font-weight:900;font-size:20px;margin-bottom:12px;">✓ {c['after_title']}</div>{a_items}
                  </div>
                </div>
                <div style="background:#090d16;color:#4ade80;border:2px solid #38bdf8;border-radius:18px;padding:22px 26px;font-family:monospace;">
                  <div style="color:#38bdf8;font-size:15px;font-weight:800;margin-bottom:8px;">LIVE SYSTEM TELEMETRY // BOLDFRAME AI LABS</div>
                  {t_items}
                </div>"""

            stats_html = "".join(
                f"<div style='background:{card_bg};border:2px solid #38bdf8;border-radius:14px;padding:16px 18px;'>"
                f"<div style='color:{sub};font-size:15px;font-weight:800;text-transform:uppercase;'>{lbl}</div>"
                f"<div style='color:#0284c7;font-family:monospace;font-size:38px;font-weight:900;margin-top:4px;'>{val}</div></div>"
                for lbl, val in c["stats"]
            )

            html = f"""<!DOCTYPE html><html><body style="margin:0;width:{w}px;height:{h}px;background:{bg};color:{fg};font-family:sans-serif;display:flex;flex-direction:column;justify-content:space-between;box-sizing:border-box;padding:{'44px 48px' if is_tall else '28px 40px'};border:5px solid {border};">
              <div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                  <span style="background:#facc15;color:#000;font-weight:900;font-size:17px;padding:7px 16px;border-radius:8px;border:2px solid #000;">{c['badge']}</span>
                  <span style="background:#0f172a;color:#38bdf8;border:2px solid #38bdf8;padding:7px 16px;border-radius:999px;font-family:monospace;font-size:15px;font-weight:800;">{c['sub_badge']}</span>
                </div>
                <h1 style="font-size:{'54px' if is_tall else '38px'};line-height:1.14;font-weight:900;margin:0;letter-spacing:-1px;">{c['headline']}</h1>
              </div>
              {middle}
              <div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px;">{stats_html}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;padding-top:12px;border-top:2px solid rgba(148,163,184,0.35);">
                  <div style="font-weight:900;font-size:19px;">Manish Hooda • BoldFrame AI Studio</div>
                  <div style="background:#0f172a;color:#facc15;font-family:monospace;font-weight:900;font-size:16px;padding:8px 18px;border-radius:10px;">SAVE THIS BLUEPRINT</div>
                </div>
              </div>
            </body></html>"""
            page = browser.new_page(viewport={"width": w, "height": h})
            page.set_content(html)
            out_path = os.path.join(ASSETS_DIR, f"post_{tag}_{key}.jpg")
            page.screenshot(path=out_path, type="jpeg", quality=92)
            page.close()
            paths[key] = out_path
        browser.close()
    return paths


def update_seo_guide_and_rss(c: dict, story_text: str, hero_url: str, today_str: str, st: dict):
    slug = f"{c['slug']}-{today_str}"
    paras = "".join(f"<p style='color:#cbd5e1;font-size:16px;line-height:1.75;margin:0 0 16px;'>{escape(p)}</p>" for p in story_text.split("\n\n") if not p.startswith("#"))
    guide_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>{escape(c['title'])} | BoldFrame AI Studio</title>
    <meta name="description" content="{escape(c['title'])}" /></head>
    <body style="margin:0;padding:24px 16px;background:#050811;color:#f8fafc;font-family:sans-serif;">
      <article style="max-width:820px;margin:0 auto;background:#0b1120;border:1px solid rgba(250,204,21,0.35);border-radius:20px;padding:32px 24px;">
        <span style="background:#facc15;color:#000;padding:4px 12px;border-radius:6px;font-size:12px;font-weight:900;">{escape(c['badge'])}</span>
        <h1 style="font-size:30px;margin:14px 0;">{escape(c['title'])}</h1>
        <img src="{hero_url}" alt="{escape(c['title'])}" style="width:100%;border-radius:14px;margin:16px 0;" />
        {paras}
        <div style="text-align:center;margin:28px 0;">
          <a href="{c['target_url']}" style="background:#facc15;color:#000;font-weight:900;padding:14px 28px;border-radius:10px;text-decoration:none;">Launch Live System &rarr;</a>
        </div>
      </article>
    </body></html>"""

    with open(os.path.join(GUIDES_DIR, f"{slug}.html"), "w") as f:
        f.write(guide_html)

    guides = st.get("published_guides", [])
    if not any(g["slug"] == slug for g in guides):
        guides.append({"slug": slug, "title": c["title"], "date": today_str, "desc": story_text[:280]})
    st["published_guides"] = guides[-40:]
    st["seo_last_date"] = today_str

    # Rebuild sitemap.xml
    urls = [f"{BASE_URL}/", f"{BASE_URL}/vault/", f"{BASE_URL}/guides/"] + [f"{BASE_URL}/guides/{g['slug']}.html" for g in st["published_guides"]]
    sm = "".join(f"  <url><loc>{u}</loc><lastmod>{today_str}</lastmod></url>\n" for u in urls)
    with open("sitemap.xml", "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>')

    # Rebuild feed.xml (for Medium RSS import / syndication)
    rss_items = "".join(
        f"  <item><title>{escape(g['title'])}</title><link>{BASE_URL}/guides/{g['slug']}.html</link>"
        f"<description>{escape(g['desc'])}</description></item>\n"
        for g in reversed(st["published_guides"][-15:])
    )
    with open("feed.xml", "w") as f:
        f.write(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f'<title>BoldFrame AI Studio</title><link>{BASE_URL}/</link>'
            f'<description>AI Inventions, Zero-Knowledge Security & Quant Systems</description>\n'
            f'{rss_items}</channel></rss>'
        )
    return f"{BASE_URL}/guides/{slug}.html"


def post_blogger(c: dict, story_text: str, hero_url: str):
    cid = os.environ.get("BLOGGER_CLIENT_ID", "").strip()
    csec = os.environ.get("BLOGGER_CLIENT_SECRET", "").strip()
    rtok = os.environ.get("BLOGGER_REFRESH_TOKEN", "").strip()
    bid = os.environ.get("BLOGGER_BLOG_ID", "").strip()
    if not all([cid, csec, rtok, bid]):
        return "SKIPPED (add BLOGGER_* secrets)"

    tok_r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={"client_id": cid, "client_secret": csec, "refresh_token": rtok, "grant_type": "refresh_token"},
        timeout=20
    )
    if not tok_r.ok:
        return f"AUTH ERROR: {tok_r.text[:160]}"
    access_token = tok_r.json()["access_token"]

    paras = "".join(f"<p>{escape(p)}</p>" for p in story_text.split("\n\n") if not p.startswith("#"))
    body_html = (
        f'<div style="max-width:820px;margin:0 auto;font-family:sans-serif;">'
        f'<img src="{hero_url}" alt="{escape(c["title"])}" style="width:100%;border-radius:14px;margin-bottom:18px;" />'
        f'{paras}'
        f'<p><a href="{c["target_url"]}" style="display:inline-block;background:#facc15;color:#000;font-weight:bold;padding:12px 24px;border-radius:8px;text-decoration:none;">Explore Live Architecture &rarr;</a></p>'
        f'</div>'
    )
    r = requests.post(
        f"https://www.googleapis.com/blogger/v3/blogs/{bid}/posts/",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"kind": "blogger#post", "title": c["title"], "content": body_html, "labels": c["labels"]},
        timeout=25
    )
    if r.ok:
        return f"LIVE: {r.json().get('url', 'published')}"
    return f"ERROR {r.status_code}: {r.text[:160]}"


def post_x(c: dict, story_text: str, img_path: str, include_link: bool):
    ak = os.environ.get("X_API_KEY", "").strip()
    aks = os.environ.get("X_API_SECRET", "").strip()
    at = os.environ.get("X_ACCESS_TOKEN", "").strip()
    ats = os.environ.get("X_ACCESS_SECRET", "").strip()
    if not all([ak, aks, at, ats]):
        return "SKIPPED (add X_* secrets)"

    import tweepy
    auth = tweepy.OAuth1UserHandler(ak, aks, at, ats)
    api_v1 = tweepy.API(auth)
    client = tweepy.Client(consumer_key=ak, consumer_secret=aks, access_token=at, access_token_secret=ats)

    first_hook = story_text.split("\n\n")[0][:190]
    tags = " ".join(f"#{t}" for t in c["labels"][:3])
    tweet_text = f"{first_hook}\n\n{tags}"
    if include_link:
        tweet_text = f"{first_hook[:155]}\n\n{c['target_url']}\n\n{tags}"

    try:
        media = api_v1.media_upload(filename=img_path)
        res = client.create_tweet(text=tweet_text[:275], media_ids=[media.media_id])
        return f"LIVE: https://x.com/i/web/status/{res.data['id']}"
    except Exception as e:
        return f"ERROR: {str(e)[:160]}"


def post_linkedin(c: dict, story_text: str, img_path: str, include_link: bool):
    tok = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    urn = os.environ.get("LINKEDIN_PERSON_URN", "").strip()
    if not all([tok, urn]):
        return "SKIPPED (add LINKEDIN_* secrets)"

    headers = {"Authorization": f"Bearer {tok}", "X-Restli-Protocol-Version": "2.0.0"}
    text = story_text + (f"\n\nLive system: {c['target_url']}" if include_link else "")

    reg = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": urn,
                "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
            }
        },
        timeout=25
    )
    if not reg.ok:
        return f"UPLOAD REG ERROR {reg.status_code}: {reg.text[:160]}"

    reg_data = reg.json()["value"]
    upload_url = reg_data["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = reg_data["asset"]

    with open(img_path, "rb") as f:
        up = requests.put(upload_url, headers={"Authorization": f"Bearer {tok}"}, data=f.read(), timeout=40)
    if not up.ok:
        return f"IMAGE PUT ERROR {up.status_code}"

    post_r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "author": urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{"status": "READY", "media": asset_urn, "title": {"text": c["title"]}}]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        },
        timeout=25
    )
    if post_r.ok:
        return f"LIVE: {post_r.headers.get('x-restli-id', 'published')}"
    return f"POST ERROR {post_r.status_code}: {post_r.text[:160]}"


def post_reddit_once_daily(c: dict, story_text: str, today_str: str, st: dict, allow_reddit: bool):
    if not allow_reddit:
        return "SKIPPED (not the 18:30 IST 1x/day slot)"
    if st.get("reddit_last_date") == today_str:
        return f"SKIPPED (already posted 1/1 for {today_str})"

    cid = os.environ.get("REDDIT_CLIENT_ID", "").strip()
    csec = os.environ.get("REDDIT_CLIENT_SECRET", "").strip()
    user = os.environ.get("REDDIT_USERNAME", "").strip()
    pw = os.environ.get("REDDIT_PASSWORD", "").strip()
    if not all([cid, csec, user, pw]):
        return "SKIPPED (add REDDIT_* secrets)"

    import praw
    try:
        reddit = praw.Reddit(
            client_id=cid, client_secret=csec,
            username=user, password=pw,
            user_agent=f"BoldFramePublisher/1.0 by u/{user}"
        )
        sub = reddit.subreddit(f"u_{user}")
        submission = sub.submit(title=c["title"][:290], selftext=f"{story_text}\n\nArchitecture link: {c['target_url']}")
        st["reddit_last_date"] = today_str
        return f"LIVE: https://reddit.com{submission.permalink}"
    except Exception as e:
        return f"ERROR: {str(e)[:160]}"


def post_medium(c: dict, story_text: str, hero_url: str):
    tok = os.environ.get("MEDIUM_TOKEN", "").strip()
    if not tok:
        return f"RSS READY ({BASE_URL}/feed.xml)"
    hdr = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    me = requests.get("https://api.medium.com/v1/me", headers=hdr, timeout=20)
    if not me.ok:
        return f"AUTH ERROR {me.status_code}"
    uid = me.json()["data"]["id"]
    md = f"![{c['title']}]({hero_url})\n\n{story_text}\n\n[Explore Live System]({c['target_url']})"
    r = requests.post(
        f"https://api.medium.com/v1/users/{uid}/posts",
        headers=hdr,
        json={"title": c["title"], "contentFormat": "markdown", "content": md, "tags": c["labels"][:5], "publishStatus": "public"},
        timeout=25
    )
    if r.ok:
        return f"LIVE: {r.json()['data'].get('url', 'published')}"
    return f"ERROR {r.status_code}: {r.text[:140]}"


def send_telegram_report(img_path: str, caption: str):
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    cid = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not tok or not cid:
        print("Telegram skipped (add TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID secrets).")
        return
    with open(img_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{tok}/sendPhoto",
            data={"chat_id": cid, "caption": caption[:1000]},
            files={"photo": f},
            timeout=30
        )


def main():
    now_ist = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)
    today_str = now_ist.strftime("%Y-%m-%d")
    override = os.environ.get("SLOT_OVERRIDE", "auto").strip().lower()

    if override == "morning" or (override == "auto" and now_ist.hour < 12):
        slot, include_link, allow_reddit, do_seo = "07:00 AM IST", False, False, True
    elif override == "evening" or (override == "auto" and 12 <= now_ist.hour < 20):
        slot, include_link, allow_reddit, do_seo = "06:30 PM IST", True, True, False
    else:
        slot, include_link, allow_reddit, do_seo = "09:00 PM IST", False, False, False

    st = load_state()
    idx = (st.get("last_idx", -1) + 1) % len(CAMPAIGNS)
    c = CAMPAIGNS[idx]
    tag = str(int(time.time()))

    story_text = refine_story_with_free_llm(c)
    imgs = render_high_ctr_images(c, tag)
    hero_url = f"{BASE_URL}/{imgs['wide']}"

    seo_res = "SKIPPED (runs on 07:00 AM slot)"
    if do_seo or st.get("seo_last_date") != today_str:
        seo_res = update_seo_guide_and_rss(c, story_text, hero_url, today_str, st)

    res_blogger  = post_blogger(c, story_text, hero_url)
    res_linkedin = post_linkedin(c, story_text, imgs["tall"], include_link)
    res_x        = post_x(c, story_text, imgs["wide"], include_link)
    res_reddit   = post_reddit_once_daily(c, story_text, today_str, st, allow_reddit)
    res_medium   = post_medium(c, story_text, hero_url)

    st["last_idx"] = idx
    save_state(st)

    report = (
        f"BoldFrame Cloud Publisher ({slot} | {today_str})\n"
        f"Campaign: {c['id']}\n\n"
        f"• SEO Guide: {seo_res}\n"
        f"• Blogger: {res_blogger}\n"
        f"• LinkedIn: {res_linkedin}\n"
        f"• X: {res_x}\n"
        f"• Reddit (1x/day): {res_reddit}\n"
        f"• Medium: {res_medium}"
    )
    print(report)
    send_telegram_report(imgs["tall"], report)


if __name__ == "__main__":
    main()
