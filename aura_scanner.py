import time
import json
import urllib.request
import urllib.parse

TG_BOT_TOKEN = "9254638108:AAHEtS8znGu7CapBSVbDZ1VT3DPtsU5qxUE"
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
            print("[✓] Telegram message delivered:", resp.status)
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

def fetch_global_visits():
    d = fetch_json("https://api.counterapi.dev/v1/hooda1_aura_quant/visits/")
    return d.get("count", "32+") if isinstance(d, dict) else "32+"

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

    # Check if the just-closed candle triggered a Dot 2-4 or SR Break trade signal
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
    print("🚀 Starting AURA Zero-Dependency 24/7 Telegram Scanner...")
    xau_1m = fetch_klines("PAXGUSDT", "1m")
    xau_5m = fetch_klines("PAXGUSDT", "5m")
    btc_1m = fetch_klines("BTCUSDT", "1m")
    visits = fetch_global_visits()

    if xau_1m and xau_5m:
        g1 = calc_locked_setup(xau_1m, XAU_BASIS)
        g5 = calc_locked_setup(xau_5m, XAU_BASIS)
        b1 = calc_locked_setup(btc_1m, 0.0) if btc_1m else None
        send_telegram(
            f"🟢 <b>AURA 24/7 TELEGRAM ENGINE RE-ARMED (WAKE-LOCK ACTIVE)</b>\n\n"
            f"👁 <b>Global Website Visits:</b> {visits}\n"
            f"📧 <b>Recent Captured Leads:</b>\n"
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

                # 1. Alert on 1m Closed-Candle Dot 2-4 / SR Break Signal
                if g1["closed_signal"] and last_alerts.get("SIG_1M_TS") != g1["closed_ts"]:
                    last_alerts["SIG_1M_TS"] = g1["closed_ts"]
                    side_lbl, entry_p, sl_p, tp1_p, tp2_p = g1["closed_signal"]
                    send_telegram(
                        f"🔥 <b>NEW GOLD 1M VIP TRADE SIGNAL ({side_lbl})</b>\n\n"
                        f"• <b>Entry (Closed 1m Bar):</b> ${entry_p}\n"
                        f"• <b>Stop-Loss:</b> ${sl_p}\n"
                        f"• <b>TP1 (Auto-BE):</b> ${tp1_p} | <b>TP2 (Runner):</b> ${tp2_p}\n"
                        f"• <b>Zones:</b> Sup ${g1['sup_zone']} / Res ${g1['res_zone']}"
                    )

                # 2. Alert when Live Price fills 1m Pending Buy/Sell Limit
                if p <= g1["buy_limit"] and last_alerts.get("XAU_1M_BUY") != g1["buy_limit"]:
                    last_alerts["XAU_1M_BUY"] = g1["buy_limit"]
                    send_telegram(
                        f"🚨 <b>GOLD 1M BUY LIMIT FILLED @ ${p}</b>\n"
                        f"• Limit: ${g1['buy_limit']} | SL: ${g1['sl_buy']} | TP1: ${g1['tp1_buy']} | TP2: ${g1['tp2_buy']}"
                    )
                elif p >= g1["sell_limit"] and last_alerts.get("XAU_1M_SELL") != g1["sell_limit"]:
                    last_alerts["XAU_1M_SELL"] = g1["sell_limit"]
                    send_telegram(
                        f"🚨 <b>GOLD 1M SELL LIMIT FILLED @ ${p}</b>\n"
                        f"• Limit: ${g1['sell_limit']} | SL: ${g1['sl_sell']} | TP1: ${g1['tp1_sell']} | TP2: ${g1['tp2_sell']}"
                    )

            # 3. Every 15 minutes (3 closed 5m bars), send updated Locked Pending Order levels if they shifted
            if xau_5m:
                g5 = calc_locked_setup(xau_5m, XAU_BASIS)
                if g5["closed_ts"] != last_5m_ts and (g5["closed_ts"] // 60000) % 15 == 0:
                    last_5m_ts = g5["closed_ts"]
                    send_telegram(
                        f"📌 <b>AURA 15-MIN LOCKED PENDING ORDER UPDATE (XAUUSD)</b>\n"
                        f"• Live Gold: <b>${g5['live_price']}</b> (Sup: ${g5['sup_zone']} / Res: ${g5['res_zone']})\n"
                        f"• <b>BUY LIMIT:</b> ${g5['buy_limit']} (SL: ${g5['sl_buy']} | TP1: ${g5['tp1_buy']})\n"
                        f"• <b>SELL LIMIT:</b> ${g5['sell_limit']} (SL: ${g5['sl_sell']} | TP1: ${g5['tp1_sell']})"
                    )

            # 4. Hourly Visitor & Stats Digest
            if now - last_hourly >= 3600 and xau_1m:
                last_hourly = now
                visits = fetch_global_visits()
                g1 = calc_locked_setup(xau_1m, XAU_BASIS)
                send_telegram(
                    f"⏰ <b>AURA HOURLY EXECUTIVE STATS & TRADES</b>\n"
                    f"• Global Website Visits: <b>{visits}</b>\n"
                    f"• XAUUSD Live: <b>${g1['live_price']}</b>\n"
                    f"• Active 1m Buy Limit: <b>${g1['buy_limit']}</b> | 1m Sell Limit: <b>${g1['sell_limit']}</b>"
                )

        except Exception as e:
            print("[!] Loop error:", e)

        time.sleep(15)

if __name__ == "__main__":
    main()
