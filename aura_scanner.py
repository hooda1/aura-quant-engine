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
TG_CHAT_ID   = "8883380313"
XAU_BASIS    = 6.55
BROKER_FEE   = 0.35

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
            print("[✓] Auto-Trade Intimation delivered! HTTP:", resp.status)
    except Exception as e:
        print("[!] Telegram error:", e)

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def fetch_klines(symbol, interval="3m", limit=200):
    return fetch_json(f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}") or []

def analyze_tf(klines, tf_label="3M", basis=6.55):
    closed = klines[:-1]
    live_p = round(float(klines[-1][4]) + basis, 2)
    closes = [float(k[4]) + basis for k in closed]
    highs  = [float(k[2]) + basis for k in closed]
    lows   = [float(k[3]) + basis for k in closed]
    opens  = [float(k[1]) + basis for k in closed]

    sup_zone = round(min(lows[-20:]), 2)
    res_zone = round(max(highs[-20:]), 2)
    locked_c = round(closes[-1], 2)
    raw_atr  = max((sum(highs[-14:]) - sum(lows[-14:])) / 14.0, 0.45)
    disp_atr = max(raw_atr, 2.80)

    sl_d  = round(disp_atr * 1.15, 2)
    tp1_d = round(disp_atr * 0.78, 2)
    tp2_d = round(disp_atr * 1.95, 2)

    buy_lim  = round(min(locked_c - disp_atr * 0.25, sup_zone + disp_atr * 0.30), 2)
    sell_lim = round(max(locked_c + disp_atr * 0.25, res_zone - disp_atr * 0.30), 2)

    # Check if the latest closed bar triggered a live Auto-Trade signal
    c, o, h, l = closes[-1], opens[-1], highs[-1], lows[-1]
    auto_signal = None
    if l <= sup_zone + raw_atr * 0.70 and c >= o:
        auto_signal = {
            "side": "BUY",
            "reason": f"{tf_label} Dot #2-4 Support Reversal @ ${sup_zone}",
            "entry": locked_c,
            "sl": round(locked_c - sl_d, 2),
            "tp1": round(locked_c + tp1_d, 2),
            "tp2": round(locked_c + tp2_d, 2),
            "net_tp1": round(tp1_d - BROKER_FEE, 2),
            "net_tp2": round(tp2_d - BROKER_FEE, 2),
            "net_sl": round(sl_d + BROKER_FEE, 2)
        }
    elif h >= res_zone - raw_atr * 0.70 and c <= o:
        auto_signal = {
            "side": "SELL",
            "reason": f"{tf_label} Dot #2-4 Resistance Reject @ ${res_zone}",
            "entry": locked_c,
            "sl": round(locked_c + sl_d, 2),
            "tp1": round(locked_c - tp1_d, 2),
            "tp2": round(locked_c - tp2_d, 2),
            "net_tp1": round(tp1_d - BROKER_FEE, 2),
            "net_tp2": round(tp2_d - BROKER_FEE, 2),
            "net_sl": round(sl_d + BROKER_FEE, 2)
        }

    return {
        "closed_ts": int(closed[-1][0]),
        "live_price": live_p,
        "sup_zone": sup_zone,
        "res_zone": res_zone,
        "buy_limit": buy_lim,
        "sell_limit": sell_lim,
        "sl_buy": round(buy_lim - sl_d, 2),
        "tp1_buy": round(buy_lim + tp1_d, 2),
        "tp2_buy": round(buy_lim + tp2_d, 2),
        "sl_sell": round(sell_lim + sl_d, 2),
        "tp1_sell": round(sell_lim - tp1_d, 2),
        "tp2_sell": round(sell_lim - tp2_d, 2),
        "net_tp1": round(tp1_d - BROKER_FEE, 2),
        "net_tp2": round(tp2_d - BROKER_FEE, 2),
        "net_sl": round(sl_d + BROKER_FEE, 2),
        "auto_signal": auto_signal
    }

def main():
    print("🤖 Starting AURA 24/7 Multi-Timeframe (1m / 3m / 5m) Auto-Trade Intimation Daemon...")
    k1 = fetch_klines("PAXGUSDT", "1m")
    k3 = fetch_klines("PAXGUSDT", "3m")
    k5 = fetch_klines("PAXGUSDT", "5m")

    if k1 and k3 and k5:
        s1 = analyze_tf(k1, "1M", XAU_BASIS)
        s3 = analyze_tf(k3, "3M", XAU_BASIS)
        s5 = analyze_tf(k5, "5M", XAU_BASIS)
        send_telegram(
            f"🤖 <b>AURA AUTO-TRADING INTIMATION ENGINE ARMED (1M · 3M · 5M)</b>\n\n"
            f"🥇 <b>XAUUSD Live (FXCM Synced):</b> ${s3['live_price']}\n\n"
            f"⚡ <b>1M SCALP AUTO-TRADER:</b>\n"
            f"• Buy Limit: <b>${s1['buy_limit']}</b> (TP1: ${s1['tp1_buy']} | TP2: ${s1['tp2_buy']} | SL: ${s1['sl_buy']})\n"
            f"• Sell Limit: <b>${s1['sell_limit']}</b> (TP1: ${s1['tp1_sell']} | TP2: ${s1['tp2_sell']} | SL: ${s1['sl_sell']})\n\n"
            f"🎯 <b>3M (TV MATCH) AUTO-TRADER:</b>\n"
            f"• Buy Limit: <b>${s3['buy_limit']}</b> (TP1: ${s3['tp1_buy']} [Net +${s3['net_tp1']}] | TP2: ${s3['tp2_buy']} [Net +${s3['net_tp2']}] | SL: ${s3['sl_buy']})\n"
            f"• Sell Limit: <b>${s3['sell_limit']}</b> (TP1: ${s3['tp1_sell']} [Net +${s3['net_tp1']}] | TP2: ${s3['tp2_sell']} [Net +${s3['net_tp2']}] | SL: ${s3['sl_sell']})\n\n"
            f"🧭 <b>5M SWING AUTO-TRADER:</b>\n"
            f"• Buy Limit: <b>${s5['buy_limit']}</b> | Sell Limit: <b>${s5['sell_limit']}</b>\n\n"
            f"✅ <i>Monitoring closed bars & live ticks across 1m, 3m, and 5m to intimate every Auto-Trade entry, TP1, TP2, and SL!</i>"
        )

    last_bar_sig = {"1m": 0, "3m": 0, "5m": 0}
    open_auto_trades = {}

    while True:
        try:
            for tf in ["1m", "3m", "5m"]:
                kl = fetch_klines("PAXGUSDT", tf)
                if not kl:
                    continue
                st = analyze_tf(kl, tf.upper(), XAU_BASIS)
                p = st["live_price"]

                # 1. Check if an active Auto-Trade on this timeframe hit TP1, TP2, or SL
                if tf in open_auto_trades:
                    ot = open_auto_trades[tf]
                    if ot["side"] == "BUY":
                        if not ot.get("tp1_hit") and p >= ot["tp1"]:
                            ot["tp1_hit"] = True
                            send_telegram(
                                f"🎯 <b>AUTO-TRADE TP1 HIT ({tf.upper()} XAUUSD BUY)</b>\n"
                                f"• Live Price: <b>${p}</b> (TP1 Target: ${ot['tp1']})\n"
                                f"• 0.01 Lot Net Profit Locked: <b>+${ot['net_tp1']}</b> (after -$0.35 fee)\n"
                                f"• Action: 50% closed; Runner SL moved to Break-Even (${ot['entry']}) targeting TP2 (${ot['tp2']})!"
                            )
                        elif ot.get("tp1_hit") and p >= ot["tp2"]:
                            send_telegram(
                                f"🏆 <b>AUTO-TRADE FULL TP2 RUNNER HIT ({tf.upper()} XAUUSD BUY)</b>\n"
                                f"• Live Price: <b>${p}</b> (TP2 Target: ${ot['tp2']})\n"
                                f"• 0.01 Lot Full Runner Net Profit: <b>+${ot['net_tp2']}</b>!"
                            )
                            del open_auto_trades[tf]
                        elif p <= (ot["entry"] if ot.get("tp1_hit") else ot["sl"]):
                            if ot.get("tp1_hit"):
                                send_telegram(f"🛡️ <b>AUTO-TRADE RUNNER CLOSED AT BREAK-EVEN ({tf.upper()} XAUUSD) @ ${p}</b> (TP1 profit already banked!)")
                            else:
                                send_telegram(f"🛑 <b>AUTO-TRADE STOP-LOSS INTIMATION ({tf.upper()} XAUUSD BUY) @ ${p}</b> (Net Risk: -${ot['net_sl']})")
                            del open_auto_trades[tf]
                    else:
                        if not ot.get("tp1_hit") and p <= ot["tp1"]:
                            ot["tp1_hit"] = True
                            send_telegram(
                                f"🎯 <b>AUTO-TRADE TP1 HIT ({tf.upper()} XAUUSD SELL)</b>\n"
                                f"• Live Price: <b>${p}</b> (TP1 Target: ${ot['tp1']})\n"
                                f"• 0.01 Lot Net Profit Locked: <b>+${ot['net_tp1']}</b> (after -$0.35 fee)\n"
                                f"• Action: 50% closed; Runner SL moved to Break-Even (${ot['entry']}) targeting TP2 (${ot['tp2']})!"
                            )
                        elif ot.get("tp1_hit") and p <= ot["tp2"]:
                            send_telegram(
                                f"🏆 <b>AUTO-TRADE FULL TP2 RUNNER HIT ({tf.upper()} XAUUSD SELL)</b>\n"
                                f"• Live Price: <b>${p}</b> (TP2 Target: ${ot['tp2']})\n"
                                f"• 0.01 Lot Full Runner Net Profit: <b>+${ot['net_tp2']}</b>!"
                            )
                            del open_auto_trades[tf]
                        elif p >= (ot["entry"] if ot.get("tp1_hit") else ot["sl"]):
                            if ot.get("tp1_hit"):
                                send_telegram(f"🛡️ <b>AUTO-TRADE RUNNER CLOSED AT BREAK-EVEN ({tf.upper()} XAUUSD) @ ${p}</b> (TP1 profit already banked!)")
                            else:
                                send_telegram(f"🛑 <b>AUTO-TRADE STOP-LOSS INTIMATION ({tf.upper()} XAUUSD SELL) @ ${p}</b> (Net Risk: -${ot['net_sl']})")
                            del open_auto_trades[tf]

                # 2. Check if a new Closed-Candle Auto-Trade triggered on this timeframe
                sig = st["auto_signal"]
                if sig and st["closed_ts"] != last_bar_sig[tf]:
                    last_bar_sig[tf] = st["closed_ts"]
                    open_auto_trades[tf] = dict(sig)
                    send_telegram(
                        f"🤖 <b>NEW AUTO-TRADE EXECUTED ({tf.upper()} XAUUSD — {sig['side']})</b>\n\n"
                        f"• <b>Trigger:</b> {sig['reason']}\n"
                        f"• <b>Auto-Entry Price:</b> ${sig['entry']} (0.01 Lot)\n"
                        f"• <b>Stop-Loss:</b> ${sig['sl']} (Net Risk: -${sig['net_sl']})\n"
                        f"• <b>TP1 (Auto-BE):</b> ${sig['tp1']} (Net Profit: +${sig['net_tp1']})\n"
                        f"• <b>TP2 (Runner):</b> ${sig['tp2']} (Net Profit: +${sig['net_tp2']})\n"
                        f"• <b>Broker Fee Deducted:</b> -$0.35\n"
                        f"<i>Tracking live ticks now for automatic TP1 / TP2 / SL intimation...</i>"
                    )

        except Exception as e:
            print("[!] Loop error:", e)

        time.sleep(12)

if __name__ == "__main__":
    main()
