import time, json, urllib.request, urllib.parse

BOT_TOKEN = "8485284049:AAH5R_4_L-zM6fB1d_R-T2t5ECf0G2nJ6K8"
CHAT_ID   = "888332620"
LAST_ALERT_TS = 0
SENT_CANDLE_IDS = set()

def send_tg(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}).encode()
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print("TG err:", e)

def fetch_klines(symbol="PAXGUSDT", interval="5m", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

print("✅ AURA Anti-Spam Scanner Started (Strict 15-min Cooldown, Closed-Candle Only)")
while True:
    try:
        now = time.time()
        # Strict 15-minute cooldown (900s) so Telegram is NEVER spammed
        if now - LAST_ALERT_TS >= 900:
            kl = fetch_klines("PAXGUSDT", "5m", 35)
            closed = kl[-2]
            c_ts = int(closed[0])
            if c_ts not in SENT_CANDLE_IDS:
                SENT_CANDLE_IDS.add(c_ts)
                # Keep set small
                if len(SENT_CANDLE_IDS) > 100:
                    SENT_CANDLE_IDS.clear()
                    SENT_CANDLE_IDS.add(c_ts)
                basis = 10.0
                closes = [float(x[4]) + basis for x in kl[:-1]]
                lows   = [float(x[3]) + basis for x in kl[:-1]]
                highs  = [float(x[2]) + basis for x in kl[:-1]]
                c = closes[-1]
                o = float(closed[1]) + basis
                sup = min(lows[-21:-1])
                res = max(highs[-21:-1])
                if c <= sup + 1.5 and c > o:
                    LAST_ALERT_TS = now
                    send_tg(
                        f"👑 <b>AURA VERIFIED 5M GOLD SIGNAL (BUY)</b>\n"
                        f"• Entry: <b>${c:.2f}</b> (ICE Spot Synced)\n"
                        f"• Support Zone: <b>${sup:.2f}</b>\n"
                        f"• TP1: <b>${c+2.50:.2f}</b> | TP2: <b>${c+5.80:.2f}</b>\n"
                        f"• SL: <b>${c-3.20:.2f}</b> | Fee: -$0.35 (0.01 Lot)"
                    )
                elif c >= res - 1.5 and c < o:
                    LAST_ALERT_TS = now
                    send_tg(
                        f"👑 <b>AURA VERIFIED 5M GOLD SIGNAL (SELL)</b>\n"
                        f"• Entry: <b>${c:.2f}</b> (ICE Spot Synced)\n"
                        f"• Resistance Zone: <b>${res:.2f}</b>\n"
                        f"• TP1: <b>${c-2.50:.2f}</b> | TP2: <b>${c-5.80:.2f}</b>\n"
                        f"• SL: <b>${c+3.20:.2f}</b> | Fee: -$0.35 (0.01 Lot)"
                    )
    except Exception as e:
        pass
    time.sleep(30)
