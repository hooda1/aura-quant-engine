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

def fetch_klines(symbol):
    try:
        r = httpx.get(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval=5m&limit=100", timeout=10)
        return r.json()
    except Exception:
        return []

def fetch_global_visits():
    try:
        r = httpx.get("https://api.counterapi.dev/v1/hooda1_aura_quant/visits/", timeout=8)
        d = r.json()
        return d.get("count", "Active")
    except Exception:
        return "Active"

def calc_locked_setup(klines, basis=0.0, is_gold=True):
    # Strictly use CLOSED candles (klines[:-1]) so signals match the website 100% and never repaint!
    closed = klines[:-1]
    live_price = round(float(klines[-1][4]) + basis, 2)

    closes = [float(k[4]) + basis for k in closed]
    highs  = [float(k[2]) + basis for k in closed]
    lows   = [float(k[3]) + basis for k in closed]

    k = 2 / 21
    ema20 = closes[0]
    for c in closes[1:]:
        ema20 = c * k + ema20 * (1 - k)

    sup_zone = round(min(lows[-20:]), 2)
    res_zone = round(max(highs[-20:]), 2)
    locked_c = round(closes[-1], 2)
    atr = max((sum(highs[-14:]) - sum(lows[-14:])) / 14.0, locked_c * 0.001)

    if is_gold:
        buy_lim  = round(min(locked_c - atr * 0.25, sup_zone + atr * 0.30), 2)
        sell_lim = round(max(locked_c + atr * 0.25, res_zone - atr * 0.30), 2)
    else:
        buy_lim  = round(min(ema20, locked_c - atr * 0.35), 2)
        sell_lim = round(max(res_zone, locked_c + atr * 0.65), 2)

    return {
        "closed_ts": int(closed[-1][0]),
        "live_price": live_price,
        "locked_close": locked_c,
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
    print("🚀 AURA v5.0 Deterministic Scanner & Hourly Digest Daemon Started...")
    xau_k = fetch_klines("PAXGUSDT")
    btc_k = fetch_klines("BTCUSDT")
    visits = fetch_global_visits()

    if xau_k and btc_k:
        gx = calc_locked_setup(xau_k, XAU_BASIS, True)
        gb = calc_locked_setup(btc_k, 0.0, False)
        send_telegram(
            f"🟢 <b>AURA v5.0 — LOCKED PENDING ORDERS & LIVE TELEMETRY</b>\n\n"
            f"👁 <b>Global Website Visits:</b> {visits}\n\n"
            f"🥇 <b>XAUUSD (Gold VIP SR Break + Dot 2-4) — Live: ${gx['live_price']}</b>\n"
            f"• Support Box: <b>${gx['sup_zone']}</b> | Resistance Box: <b>${gx['res_zone']}</b>\n"
            f"• <b>BUY LIMIT:</b> ${gx['buy_limit']} (SL: ${gx['sl_buy']} | TP1: ${gx['tp1_buy']} | TP2: ${gx['tp2_buy']})\n"
            f"• <b>SELL LIMIT:</b> ${gx['sell_limit']} (SL: ${gx['sl_sell']} | TP1: ${gx['tp1_sell']} | TP2: ${gx['tp2_sell']})\n\n"
            f"₿ <b>BTCUSD (Core Institutional) — Live: ${gb['live_price']}</b>\n"
            f"• <b>BUY LIMIT:</b> ${gb['buy_limit']} (SL: ${gb['sl_buy']} | TP1: ${gb['tp1_buy']})\n"
            f"• <b>SELL LIMIT:</b> ${gb['sell_limit']} (SL: ${gb['sl_sell']} | TP1: ${gb['tp1_sell']})"
        )

    last_alerts = {}
    last_hourly_ping = time.time()

    while True:
        try:
            now = time.time()
            xau_k = fetch_klines("PAXGUSDT")
            btc_k = fetch_klines("BTCUSDT")

            if xau_k:
                gx = calc_locked_setup(xau_k, XAU_BASIS, True)
                p = gx["live_price"]
                if p <= gx["buy_limit"] and last_alerts.get("XAU_BUY") != gx["buy_limit"]:
                    last_alerts["XAU_BUY"] = gx["buy_limit"]
                    send_telegram(
                        f"🚨 <b>GOLD VIP (SR + DOT 2-4) BUY LIMIT FILLED!</b>\n\n"
                        f"• <b>Entry Price:</b> ${p} (Limit: ${gx['buy_limit']})\n"
                        f"• <b>Support Zone:</b> ${gx['sup_zone']}\n"
                        f"• <b>Stop-Loss:</b> ${gx['sl_buy']} | <b>TP1 (Auto-BE):</b> ${gx['tp1_buy']} | <b>TP2:</b> ${gx['tp2_buy']}"
                    )
                elif p >= gx["sell_limit"] and last_alerts.get("XAU_SELL") != gx["sell_limit"]:
                    last_alerts["XAU_SELL"] = gx["sell_limit"]
                    send_telegram(
                        f"🚨 <b>GOLD VIP (SR + DOT 2-4) SELL LIMIT FILLED!</b>\n\n"
                        f"• <b>Entry Price:</b> ${p} (Limit: ${gx['sell_limit']})\n"
                        f"• <b>Resistance Zone:</b> ${gx['res_zone']}\n"
                        f"• <b>Stop-Loss:</b> ${gx['sl_sell']} | <b>TP1 (Auto-BE):</b> ${gx['tp1_sell']} | <b>TP2:</b> ${gx['tp2_sell']}"
                    )

            if btc_k:
                gb = calc_locked_setup(btc_k, 0.0, False)
                p = gb["live_price"]
                if p <= gb["buy_limit"] and last_alerts.get("BTC_BUY") != gb["buy_limit"]:
                    last_alerts["BTC_BUY"] = gb["buy_limit"]
                    send_telegram(f"🚨 <b>BTCUSD BUY LIMIT FILLED @ ${p}</b>\n• Limit: ${gb['buy_limit']} | SL: ${gb['sl_buy']} | TP1: ${gb['tp1_buy']}")
                elif p >= gb["sell_limit"] and last_alerts.get("BTC_SELL") != gb["sell_limit"]:
                    last_alerts["BTC_SELL"] = gb["sell_limit"]
                    send_telegram(f"🚨 <b>BTCUSD SELL LIMIT FILLED @ ${p}</b>\n• Limit: ${gb['sell_limit']} | SL: ${gb['sl_sell']} | TP1: ${gb['tp1_sell']}")

            # HOURLY DIGEST REPORT EVERY 3600 SECONDS (1 HOUR)
            if now - last_hourly_ping >= 3600 and xau_k and btc_k:
                last_hourly_ping = now
                visits = fetch_global_visits()
                gx = calc_locked_setup(xau_k, XAU_BASIS, True)
                gb = calc_locked_setup(btc_k, 0.0, False)
                send_telegram(
                    f"⏰ <b>AURA HOURLY EXECUTIVE DIGEST & PENDING ORDERS</b>\n\n"
                    f"👁 <b>Cumulative Website Visits:</b> {visits}\n"
                    f"🥇 <b>XAUUSD Live:</b> ${gx['live_price']} (Sup: ${gx['sup_zone']} / Res: ${gx['res_zone']})\n"
                    f"   • Locked Buy Limit: <b>${gx['buy_limit']}</b> | TP1: ${gx['tp1_buy']}\n"
                    f"   • Locked Sell Limit: <b>${gx['sell_limit']}</b> | TP1: ${gx['tp1_sell']}\n"
                    f"₿ <b>BTCUSD Live:</b> ${gb['live_price']}\n"
                    f"   • Locked Buy Limit: <b>${gb['buy_limit']}</b> | Locked Sell Limit: <b>${gb['sell_limit']}</b>"
                )

        except Exception as e:
            print("[!] Loop exception:", e)

        time.sleep(20)

if __name__ == "__main__":
    main()
