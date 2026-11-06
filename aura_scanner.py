import time
import httpx

TG_BOT_TOKEN = "9254638108:AAHEtS8znGu7CapBSVbDZ1VT3DPtsU5qxUE"
TG_CHAT_ID = "8883380313"
XAU_BASIS = 3.45

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        httpx.post(url, json={"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=10)
    except Exception as e:
        print("[!] Telegram error:", e)

def fetch_klines(symbol, interval="1m"):
    try:
        r = httpx.get(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit=100", timeout=10)
        return r.json()
    except Exception:
        return []

def fetch_global_visits():
    try:
        r = httpx.get("https://api.counterapi.dev/v1/hooda1_aura_quant/visits/", timeout=8)
        return r.json().get("count", "Active")
    except Exception:
        return "Active"

def calc_locked_setup(klines, basis=0.0, is_gold=True):
    closed = klines[:-1]
    live_price = round(float(klines[-1][4]) + basis, 2)
    closes = [float(k[4]) + basis for k in closed]
    highs  = [float(k[2]) + basis for k in closed]
    lows   = [float(k[3]) + basis for k in closed]

    sup_zone = round(min(lows[-20:]), 2)
    res_zone = round(max(highs[-20:]), 2)
    locked_c = round(closes[-1], 2)
    atr = max((sum(highs[-14:]) - sum(lows[-14:])) / 14.0, locked_c * 0.0008)

    buy_lim  = round(min(locked_c - atr * 0.25, sup_zone + atr * 0.30), 2)
    sell_lim = round(max(locked_c + atr * 0.25, res_zone - atr * 0.30), 2)

    return {
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
        "tp2_sell": round(sell_lim - atr * 1.75, 2)
    }

def main():
    print("🚀 AURA 1m + 5m Dual-Timeframe Gold VIP Scanner Started...")
    xau_1m = fetch_klines("PAXGUSDT", "1m")
    xau_5m = fetch_klines("PAXGUSDT", "5m")
    visits = fetch_global_visits()

    if xau_1m and xau_5m:
        g1 = calc_locked_setup(xau_1m, XAU_BASIS, True)
        g5 = calc_locked_setup(xau_5m, XAU_BASIS, True)
        send_telegram(
            f"🟢 <b>AURA 1M & 5M GOLD VIP (SR + DOT 2-4) SCANNER ARMED</b>\n\n"
            f"👁 <b>Global Website Visits:</b> {visits}\n"
            f"🥇 <b>XAUUSD Live (FXCM Calibrated):</b> ${g1['live_price']}\n\n"
            f"⚡ <b>1-MINUTE (1m) SCALP LOCKED ORDERS:</b>\n"
            f"• 1m Support: <b>${g1['sup_zone']}</b> | 1m Resistance: <b>${g1['res_zone']}</b>\n"
            f"• <b>BUY LIMIT:</b> ${g1['buy_limit']} (SL: ${g1['sl_buy']} | TP1: ${g1['tp1_buy']} | TP2: ${g1['tp2_buy']})\n"
            f"• <b>SELL LIMIT:</b> ${g1['sell_limit']} (SL: ${g1['sl_sell']} | TP1: ${g1['tp1_sell']} | TP2: ${g1['tp2_sell']})\n\n"
            f"🧭 <b>5-MINUTE (5m) SWING LOCKED ORDERS:</b>\n"
            f"• 5m Support: <b>${g5['sup_zone']}</b> | 5m Resistance: <b>${g5['res_zone']}</b>\n"
            f"• <b>BUY LIMIT:</b> ${g5['buy_limit']} (SL: ${g5['sl_buy']} | TP1: ${g5['tp1_buy']})\n"
            f"• <b>SELL LIMIT:</b> ${g5['sell_limit']} (SL: ${g5['sl_sell']} | TP1: ${g5['tp1_sell']})"
        )

    last_alerts = {}
    last_hourly = time.time()

    while True:
        try:
            now = time.time()
            xau_1m = fetch_klines("PAXGUSDT", "1m")
            if xau_1m:
                g1 = calc_locked_setup(xau_1m, XAU_BASIS, True)
                p = g1["live_price"]
                if p <= g1["buy_limit"] and last_alerts.get("XAU_1M_BUY") != g1["buy_limit"]:
                    last_alerts["XAU_1M_BUY"] = g1["buy_limit"]
                    send_telegram(
                        f"🚨 <b>GOLD 1M VIP (SR + DOT 2-4) BUY LIMIT FILLED!</b>\n\n"
                        f"• <b>Entry Price:</b> ${p} (1m Limit: ${g1['buy_limit']})\n"
                        f"• <b>1m Support Box:</b> ${g1['sup_zone']}\n"
                        f"• <b>SL:</b> ${g1['sl_buy']} | <b>TP1 (Auto-BE):</b> ${g1['tp1_buy']} | <b>TP2:</b> ${g1['tp2_buy']}"
                    )
                elif p >= g1["sell_limit"] and last_alerts.get("XAU_1M_SELL") != g1["sell_limit"]:
                    last_alerts["XAU_1M_SELL"] = g1["sell_limit"]
                    send_telegram(
                        f"🚨 <b>GOLD 1M VIP (SR + DOT 2-4) SELL LIMIT FILLED!</b>\n\n"
                        f"• <b>Entry Price:</b> ${p} (1m Limit: ${g1['sell_limit']})\n"
                        f"• <b>1m Resistance Box:</b> ${g1['res_zone']}\n"
                        f"• <b>SL:</b> ${g1['sl_sell']} | <b>TP1 (Auto-BE):</b> ${g1['tp1_sell']} | <b>TP2:</b> ${g1['tp2_sell']}"
                    )

            if now - last_hourly >= 3600 and xau_1m:
                last_hourly = now
                visits = fetch_global_visits()
                g1 = calc_locked_setup(xau_1m, XAU_BASIS, True)
                send_telegram(
                    f"⏰ <b>AURA HOURLY DIGEST (1M GOLD VIP)</b>\n"
                    f"• Visits: {visits} | XAUUSD: ${g1['live_price']}\n"
                    f"• 1m Buy Limit: ${g1['buy_limit']} | 1m Sell Limit: ${g1['sell_limit']}"
                )
        except Exception as e:
            print("[!] Loop error:", e)

        time.sleep(15)

if __name__ == "__main__":
    main()
