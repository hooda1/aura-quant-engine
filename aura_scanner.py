import os
import time
import json
import urllib.request
import urllib.parse

def load_env_token():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("TG_BOT_TOKEN="):
                    return line.strip().split("=", 1)[1].strip()
    return os.environ.get("TG_BOT_TOKEN", "")

TG_BOT_TOKEN = load_env_token()
TG_CHAT_ID = "8883380313"
XAU_BASIS = 3.45

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TG_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("[✓] Telegram message delivered! HTTP:", resp.status)
    except Exception as e:
        print("[!] Telegram error:", e)

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print("[!] Fetch error:", e)
        return None

def fetch_klines(symbol, interval="1m"):
    return fetch_json(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit=100") or []

def calc_locked_setup(klines, basis=0.0):
    closed = klines[:-1]
    live_price = round(float(klines[-1][4]) + basis, 2)
    closes = [float(k[4]) + basis for k in closed]
    highs  = [float(k[2]) + basis for k in closed]
    lows   = [float(k[3]) + basis for k in closed]
    opens  = [float(k[1]) + basis for k in closed]

    sup_zone = round(min(lows[-20:]), 2)
    res_zone = round(max(highs[-20:]), 2)
    locked_c = round(closes[-1], 2)
    atr = max((sum(highs[-14:]) - sum(lows[-14:])) / 14.0, locked_c * 0.0008)

    buy_lim  = round(min(locked_c - atr * 0.25, sup_zone + atr * 0.30), 2)
    sell_lim = round(max(locked_c + atr * 0.25, res_zone - atr * 0.30), 2)

    signal = None
    if lows[-1] <= sup_zone + atr * 0.55 and closes[-1] > opens[-1]:
        signal = ("BUY (Dot #2-4 Support Reversal)", locked_c, round(locked_c - atr * 1.35, 2), round(locked_c + atr * 0.68, 2), round(locked_c + atr * 1.75, 2))
    elif highs[-1] >= res_zone - atr * 0.55 and closes[-1] < opens[-1]:
        signal = ("SELL (Dot #2-4 Resistance Reject)", locked_c, round(locked_c + atr * 1.35, 2), round(locked_c - atr * 0.68, 2), round(locked_c - atr * 1.75, 2))

    return {
        "closed_ts": int(closed[-1][0]),
        "live_price": live_price,
        "sup_zone": sup_zone,
        "res_zone": res_zone,
        "buy_limit": buy_lim,
        "sell_limit": sell_lim,
        "sl_buy": round(buy_lim - atr * 1.35, 2),
        "tp1_buy": round(buy_lim + atr * 0.68, 2),
        "tp2_buy": round(buy_lim + atr * 1.75, 2),
        "sl_sell": round(sell_lim + atr * 1.35, 2),
        "tp1_sell": round(sell_lim - atr * 0.68, 2),
        "tp2_sell": round(sell_lim - atr * 1.75, 2),
        "closed_signal": signal
    }

def main():
    print("🚀 Starting AURA 24/7 Telegram Scanner (Protected Token Mode)...")
    xau_1m = fetch_klines("PAXGUSDT", "1m")
    xau_5m = fetch_klines("PAXGUSDT", "5m")

    if xau_1m and xau_5m:
        g1 = calc_locked_setup(xau_1m, XAU_BASIS)
        g5 = calc_locked_setup(xau_5m, XAU_BASIS)
        send_telegram(
            f"🟢 <b>AURA 24/7 TELEGRAM ENGINE ONLINE (PROTECTED TOKEN)</b>\n\n"
            f"📧 <b>Synced VIP Subscriber Leads:</b>\n"
            f"• manishkumarhooda23@gmail.com (+917011169545) — Gold 1m/5m VIP\n"
            f"• manishkumarhooda0@gmail.com (+917011169545) — Gold 1m/5m VIP\n\n"
            f"🥇 <b>XAUUSD 1M SCALP (SR Break + Dot 2-4) — Live: ${g1['live_price']}</b>\n"
            f"• 1m Support Box: <b>${g1['sup_zone']}</b> | 1m Resistance Box: <b>${g1['res_zone']}</b>\n"
            f"• <b>BUY LIMIT:</b> ${g1['buy_limit']} | SL: ${g1['sl_buy']} | TP1: ${g1['tp1_buy']} | TP2: ${g1['tp2_buy']}\n"
            f"• <b>SELL LIMIT:</b> ${g1['sell_limit']} | SL: ${g1['sl_sell']} | TP1: ${g1['tp1_sell']} | TP2: ${g1['tp2_sell']}\n\n"
            f"🧭 <b>XAUUSD 5M SWING LOCKED ORDERS:</b>\n"
            f"• <b>BUY LIMIT:</b> ${g5['buy_limit']} (SL: ${g5['sl_buy']} | TP1: ${g5['tp1_buy']})\n"
            f"• <b>SELL LIMIT:</b> ${g5['sell_limit']} (SL: ${g5['sl_sell']} | TP1: ${g5['tp1_sell']})"
        )

    last_alerts = {}
    last_5m_ts = 0
    last_hourly = time.time()

    while True:
        try:
            now = time.time()
            xau_1m = fetch_klines("PAXGUSDT", "1m")
            xau_5m = fetch_klines("PAXGUSDT", "5m")

            if xau_1m:
                g1 = calc_locked_setup(xau_1m, XAU_BASIS)
                p = g1["live_price"]

                if g1["closed_signal"] and last_alerts.get("SIG_1M_TS") != g1["closed_ts"]:
                    last_alerts["SIG_1M_TS"] = g1["closed_ts"]
                    side_lbl, entry_p, sl_p, tp1_p, tp2_p = g1["closed_signal"]
                    send_telegram(
                        f"🔥 <b>NEW GOLD 1M VIP TRADE SIGNAL ({side_lbl})</b>\n\n"
                        f"• <b>Entry (Closed 1m Bar):</b> ${entry_p}\n"
                        f"• <b>Stop-Loss:</b> ${sl_p} | <b>TP1 (Auto-BE):</b> ${tp1_p} | <b>TP2:</b> ${tp2_p}\n"
                        f"• <b>Zones:</b> Sup ${g1['sup_zone']} / Res ${g1['res_zone']}"
                    )

                if p <= g1["buy_limit"] and last_alerts.get("XAU_1M_BUY") != g1["buy_limit"]:
                    last_alerts["XAU_1M_BUY"] = g1["buy_limit"]
                    send_telegram(f"🚨 <b>GOLD 1M BUY LIMIT FILLED @ ${p}</b>\n• Limit: ${g1['buy_limit']} | SL: ${g1['sl_buy']} | TP1: ${g1['tp1_buy']} | TP2: ${g1['tp2_buy']}")
                elif p >= g1["sell_limit"] and last_alerts.get("XAU_1M_SELL") != g1["sell_limit"]:
                    last_alerts["XAU_1M_SELL"] = g1["sell_limit"]
                    send_telegram(f"🚨 <b>GOLD 1M SELL LIMIT FILLED @ ${p}</b>\n• Limit: ${g1['sell_limit']} | SL: ${g1['sl_sell']} | TP1: ${g1['tp1_sell']} | TP2: ${g1['tp2_sell']}")

            if xau_5m:
                g5 = calc_locked_setup(xau_5m, XAU_BASIS)
                if g5["closed_ts"] != last_5m_ts and (g5["closed_ts"] // 60000) % 5 == 0:
                    last_5m_ts = g5["closed_ts"]
                    send_telegram(
                        f"📌 <b>AURA 5-MIN LOCKED PENDING ORDER UPDATE (XAUUSD)</b>\n"
                        f"• Live Gold: <b>${g5['live_price']}</b> (Sup: ${g5['sup_zone']} / Res: ${g5['res_zone']})\n"
                        f"• <b>1m/5m BUY LIMIT:</b> ${g5['buy_limit']} (SL: ${g5['sl_buy']} | TP1: ${g5['tp1_buy']})\n"
                        f"• <b>1m/5m SELL LIMIT:</b> ${g5['sell_limit']} (SL: ${g5['sl_sell']} | TP1: ${g5['tp1_sell']})"
                    )

            if now - last_hourly >= 3600 and xau_1m:
                last_hourly = now
                g1 = calc_locked_setup(xau_1m, XAU_BASIS)
                send_telegram(f"⏰ <b>AURA HOURLY DIGEST</b>\n• XAUUSD Live: <b>${g1['live_price']}</b>\n• Active 1m Buy Limit: <b>${g1['buy_limit']}</b> | 1m Sell Limit: <b>${g1['sell_limit']}</b>")

        except Exception as e:
            print("[!] Loop error:", e)

        time.sleep(15)

if __name__ == "__main__":
    main()
