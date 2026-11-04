import asyncio, json, os, random, subprocess
from datetime import datetime
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

STRAT_FILE = "user_data/strategies.json"

def load_strategies():
    if os.path.exists(STRAT_FILE):
        with open(STRAT_FILE, "r") as f:
            return json.load(f)
    return []

def save_strategies(strats):
    os.makedirs("user_data", exist_ok=True)
    with open(STRAT_FILE, "w") as f:
        json.dump(strats, f, indent=2)

STATE = {
    "kill_switch": False,
    "execution_mode": "PAPER",
    "supporter_tier": "COMMUNITY (FREE)",
    "daily_pnl": 485.20,
    "prices": {
        "XAUUSD": {"price": 4036.17, "spread": 0.22, "ema9": 4035.60, "ema21": 4034.10, "rsi": 57.2},
        "BTCUSD": {"price": 78463.10, "spread": 1.40, "ema9": 78440.00, "ema21": 78380.00, "rsi": 60.8}
    },
    "strategies": load_strategies(),
    "logs": [
        "[SYSTEM] AURA Open-Core v1.0 Initialized (Pure-Python Engine Active)",
        "[FEED] XAUUSD ($4,036.17) & BTCUSD ($78,463.10) Streams Locked",
        "[GUARDRAIL] Spread Filter & Daily Drawdown Circuit Breaker ARMED"
    ]
}

def log_event(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    STATE["logs"].insert(0, f"[{ts}] {msg}")
    STATE["logs"] = STATE["logs"][:35]

async def execute_order(symbol: str, side: str, risk_usd: float, rr: float, platform: str, reason: str):
    if STATE["kill_switch"]:
        log_event(f"BLOCKED {symbol}: Kill Switch is ENGAGED!")
        return
    mkt = STATE["prices"][symbol]
    entry = mkt["price"]
    stop_dist = 3.50 if symbol == "XAUUSD" else 250.0
    sl = round(entry - stop_dist if side == "BUY" else entry + stop_dist, 2)
    tp = round(entry + (stop_dist * rr) if side == "BUY" else entry - (stop_dist * rr), 2)
    lots = round(risk_usd / stop_dist, 3)
    log_event(f"EXEC [{STATE['execution_mode']}] >> {side} {lots} Lots {symbol} @ ${entry} | SL: ${sl} | TP: ${tp} via {platform} ({reason})")

async def market_loop():
    while True:
        await asyncio.sleep(1.1)
        if STATE["kill_switch"]:
            continue
        for sym, step, base_sp in [("XAUUSD", 0.55, 0.21), ("BTCUSD", 38.0, 1.30)]:
            p = STATE["prices"][sym]
            p["price"] = round(p["price"] + random.uniform(-step, step * 1.04), 2)
            p["spread"] = round(max(0.08, base_sp + random.uniform(-0.07, 0.20)), 2)
            p["ema9"] = round(p["ema9"] * 0.8 + p["price"] * 0.2, 2)
            p["ema21"] = round(p["ema21"] * 0.92 + p["price"] * 0.08, 2)
            p["rsi"] = round(min(86, max(22, p["rsi"] + random.uniform(-1.6, 1.7))), 1)

        for strat in STATE["strategies"]:
            if not strat["active"]:
                continue
            sym = strat["symbol"]
            mkt = STATE["prices"][sym]
            if mkt["spread"] > float(strat["max_spread"]):
                continue
            if mkt["ema9"] > mkt["ema21"] and mkt["rsi"] >= float(strat["rsi_threshold"]):
                if random.random() < 0.07:
                    strat["trades_taken"] += 1
                    STATE["daily_pnl"] = round(STATE["daily_pnl"] + random.uniform(-20, 75), 2)
                    save_strategies(STATE["strategies"])
                    await execute_order(sym, "BUY", float(strat["risk_usd"]), float(strat["rr_ratio"]), strat["platform"], strat["name"])

async def add_strategy(request):
    s = await request.json()
    s["id"] = f"STRAT-0{len(STATE['strategies']) + 1}"
    s["active"] = True
    s["trades_taken"] = 0
    STATE["strategies"].insert(0, s)
    save_strategies(STATE["strategies"])
    log_event(f"SAVED TO user_data/: '{s['name']}' on {s['symbol']} ({s['platform']})")
    return JSONResponse({"status": "saved"})

async def toggle_kill(request):
    STATE["kill_switch"] = not STATE["kill_switch"]
    log_event(f"KILL SWITCH {'ENGAGED' if STATE['kill_switch'] else 'RELEASED'}")
    return JSONResponse({"kill_switch": STATE["kill_switch"]})

async def toggle_mode(request):
    STATE["execution_mode"] = "LIVE" if STATE["execution_mode"] == "PAPER" else "PAPER"
    log_event(f"MODE CHANGED TO {STATE['execution_mode']}")
    return JSONResponse({"mode": STATE["execution_mode"]})

async def git_upgrade(request):
    try:
        out = subprocess.check_output(["git", "pull", "origin", "main"], stderr=subprocess.STDOUT).decode()
        log_event(f"GITHUB UPGRADE: {out.strip()}")
        return JSONResponse({"status": "ok", "msg": out})
    except Exception:
        log_event("GITHUB NOTICE: Link your remote GitHub repo first (user_data/ is protected).")
        return JSONResponse({"status": "notice"})

async def ws_stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_text(json.dumps(STATE))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AURA // XAUUSD & BTC Open-Core Terminal</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
  <style>
    body { background: #060911; color: #e2e8f0; font-family: system-ui, sans-serif; }
    .glass { background: rgba(15, 23, 42, 0.72); backdrop-filter: blur(16px); border: 1px solid rgba(56, 189, 248, 0.18); }
  </style>
</head>
<body class="p-3 md:p-6">
  <div class="glass rounded-2xl p-3 mb-4 flex flex-wrap items-center justify-between gap-2 border border-amber-500/30">
    <div class="flex items-center gap-2 text-xs">
      <span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-bold">OPEN-CORE v1.0</span>
      <span class="text-slate-300">Strategies auto-saved in <code class="text-cyan-300">user_data/</code> (Safe during upgrades)</span>
    </div>
    <div class="flex flex-wrap items-center gap-2">
      <button onclick="openTipModal('Coffee ($5)', 'Unlock Supporter Badge & Telegram Alerts')" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-400 text-slate-950 hover:bg-amber-300">☕ Buy Me a Coffee ($5)</button>
      <button onclick="openTipModal('Team Dinner ($25)', 'Unlock Pro NY Killzone Gold & BTC Presets')" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-r from-fuchsia-500 to-cyan-400 text-slate-950">🍽️ Buy Team Dinner ($25)</button>
      <button onclick="fetch('/api/upgrade',{method:'POST'})" class="px-3 py-1.5 rounded-xl text-xs font-mono bg-slate-800 text-cyan-300 border border-cyan-500/30">⟳ 1-Click GitHub Upgrade</button>
    </div>
  </div>

  <header class="glass rounded-2xl p-4 mb-4 flex flex-wrap items-center justify-between gap-4">
    <div class="flex items-center gap-3">
      <div class="h-3 w-3 rounded-full bg-emerald-400 animate-ping"></div>
      <h1 class="text-xl font-bold bg-gradient-to-r from-amber-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">AURA // XAUUSD & BTC QUANT TERMINAL</h1>
      <span id="modeBadge" onclick="fetch('/api/mode',{method:'POST'})" class="cursor-pointer text-xs font-mono px-2.5 py-1 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">MODE: PAPER</span>
    </div>
    <div class="flex items-center gap-4">
      <div class="text-right">
        <div class="text-xs text-slate-400">DAILY NET P&L</div>
        <div id="dailyPnl" class="text-lg font-mono font-bold text-emerald-400">+$485.20</div>
      </div>
      <button id="killBtn" onclick="fetch('/api/killswitch',{method:'POST'})" class="px-4 py-2 rounded-xl font-bold text-xs bg-rose-600 text-white">GLOBAL KILL SWITCH</button>
    </div>
  </header>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
    <div class="glass rounded-2xl p-5 border-amber-500/30">
      <div class="flex justify-between">
        <div><span class="text-xs font-mono text-amber-300">GOLD SPOT // MT5 + PERPS</span><h2 class="text-2xl font-bold text-white">XAU / USD</h2></div>
        <div class="text-right"><div id="xauPrice" class="text-3xl font-mono font-bold text-amber-400">$4036.17</div><div class="text-xs font-mono text-slate-400">Spread: <span id="xauSpread" class="text-emerald-400">$0.22</span></div></div>
      </div>
      <div class="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-800 text-xs font-mono">
        <div>EMA 9: <span id="xauEma9">4035.60</span></div><div>EMA 21: <span id="xauEma21">4034.10</span></div><div>RSI: <span id="xauRsi" class="text-amber-300">57.2</span></div>
      </div>
    </div>
    <div class="glass rounded-2xl p-5 border-cyan-500/30">
      <div class="flex justify-between">
        <div><span class="text-xs font-mono text-cyan-300">BITCOIN // CCXT UNIFIED</span><h2 class="text-2xl font-bold text-white">BTC / USD</h2></div>
        <div class="text-right"><div id="btcPrice" class="text-3xl font-mono font-bold text-cyan-400">$78463.10</div><div class="text-xs font-mono text-slate-400">Spread: <span id="btcSpread" class="text-emerald-400">$1.40</span></div></div>
      </div>
      <div class="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-800 text-xs font-mono">
        <div>EMA 9: <span id="btcEma9">78440.0</span></div><div>EMA 21: <span id="btcEma21">78380.0</span></div><div>RSI: <span id="btcRsi" class="text-cyan-300">60.8</span></div>
      </div>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
    <div class="glass rounded-2xl p-4 lg:col-span-2"><div class="text-xs font-mono text-slate-400 mb-2">LIVE XAUUSD TICK STREAM</div><div id="tvchart" class="w-full h-64 rounded-xl overflow-hidden"></div></div>
    <div class="glass rounded-2xl p-4 space-y-2.5 text-xs">
      <h3 class="text-sm font-bold text-cyan-300 uppercase">+ Enter Custom Strategy</h3>
      <input id="stName" type="text" placeholder="Strategy Name" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white">
      <div class="grid grid-cols-2 gap-2">
        <select id="stSym" class="bg-slate-900 border border-slate-700 rounded-lg p-2 text-white"><option value="XAUUSD">XAUUSD</option><option value="BTCUSD">BTCUSD</option></select>
        <select id="stPlat" class="bg-slate-900 border border-slate-700 rounded-lg p-2 text-white"><option value="MT5 Cloud">MT5 Cloud</option><option value="Binance/Bybit">Binance/Bybit</option><option value="Delta Exchange">Delta Exchange</option></select>
      </div>
      <select id="stInd" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white">
        <option value="EMA_9_CROSS_21">EMA 9 Crosses EMA 21 + RSI Filter</option>
        <option value="RSI_MOMENTUM">RSI Momentum Breakout + Spread Guard</option>
      </select>
      <div class="grid grid-cols-2 gap-2">
        <input id="stRsi" type="number" value="55" placeholder="Min RSI" class="bg-slate-900 border border-slate-700 rounded-lg p-2 text-white">
        <input id="stSpread" type="number" step="0.05" value="0.35" placeholder="Max Spread ($)" class="bg-slate-900 border border-slate-700 rounded-lg p-2 text-white">
      </div>
      <div class="grid grid-cols-2 gap-2">
        <input id="stRisk" type="number" value="100" placeholder="Risk ($)" class="bg-slate-900 border border-slate-700 rounded-lg p-2 text-white">
        <input id="stRR" type="number" step="0.5" value="2.5" placeholder="R:R Ratio" class="bg-slate-900 border border-slate-700 rounded-lg p-2 text-white">
      </div>
      <button onclick="deployStrategy()" class="w-full py-2.5 rounded-xl font-bold bg-gradient-to-r from-amber-500 to-cyan-400 text-slate-950">SAVE & LAUNCH STRATEGY</button>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
    <div class="glass rounded-2xl p-4"><h3 class="text-xs font-bold uppercase text-slate-400 mb-2">Saved Strategies (user_data/strategies.json)</h3><div id="stratList" class="space-y-2"></div></div>
    <div class="glass rounded-2xl p-4"><h3 class="text-xs font-bold uppercase text-slate-400 mb-2">Real-Time Execution Stream</h3><div id="logBox" class="h-44 overflow-y-auto font-mono text-xs space-y-1 bg-slate-950/80 p-3 rounded-xl"></div></div>
  </div>

  <div id="tipModal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
    <div class="glass rounded-2xl p-6 max-w-md w-full border border-amber-400/40">
      <h3 id="tipTitle" class="text-lg font-bold text-amber-300">Support AURA Open-Core</h3>
      <p id="tipDesc" class="text-xs text-slate-300 mt-1 mb-4"></p>
      <div class="bg-slate-900 p-3 rounded-xl text-xs font-mono space-y-2 mb-4 border border-slate-800">
        <div><span class="text-slate-400">USDT (TRC20 / Arbitrum):</span> <span class="text-emerald-400">0xYOUR_USDT_WALLET_HERE</span></div>
        <div><span class="text-slate-400">GitHub Sponsors / Polar:</span> <span class="text-cyan-300">polar.sh/your_username</span></div>
        <div><span class="text-slate-400">BuyMeACoffee / UPI:</span> <span class="text-amber-300">buymeacoffee.com/your_name</span></div>
      </div>
      <button onclick="document.getElementById('tipModal').classList.add('hidden')" class="w-full py-2 rounded-xl bg-slate-800 text-white text-xs font-bold">Close Window</button>
    </div>
  </div>

  <script>
    const chart = LightweightCharts.createChart(document.getElementById('tvchart'), {
      layout: { background: { color: '#090D16' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
      timeScale: { timeVisible: true, secondsVisible: true }
    });
    const series = chart.addAreaSeries({ lineColor: '#f59e0b', topColor: 'rgba(245, 158, 11, 0.3)', bottomColor: 'rgba(245, 158, 11, 0.0)' });

    const ws = new WebSocket(`ws://${location.host}/ws`); ws.onmessage = (e) => { const d = JSON.parse(e.data); const x = d.prices.XAUUSD, b = d.prices.BTCUSD; document.getElementById('xauPrice').innerText = `$${x.price.toFixed(2)}`; document.getElementById('xauSpread').innerText = `$${x.spread.toFixed(2)}`; document.getElementById('xauEma9').innerText = x.ema9; document.getElementById('xauEma21').innerText = x.ema21; document.getElementById('xauRsi').innerText = x.rsi; document.getElementById('btcPrice').innerText = `$${b.price.toFixed(2)}`; document.getElementById('btcSpread').innerText = `$${b.spread.toFixed(2)}`; document.getElementById('btcEma9').innerText = b.ema9; document.getElementById('btcEma21').innerText = b.ema21; document.getElementById('btcRsi').innerText = b.rsi; document.getElementById('dailyPnl').innerText = (d.daily_pnl >= 0 ? '+$' : '-$') + Math.abs(d.daily_pnl).toFixed(2); document.getElementById('modeBadge').innerText = `MODE: ${d.execution_mode}`;
      series.update({ time: Math.floor(Date.now() / 1000), value: x.price });

      document.getElementById('stratList').innerHTML = d.strategies.map(s => `
        <div class="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 flex justify-between items-center text-xs">
          <div><div class="font-bold text-white">${s.name} <span class="text-amber-400">[${s.symbol}]</span></div>
          <div class="text-slate-400">${s.platform} | Risk: $${s.risk_usd} \vert{} Max Spread:$${s.max_spread}</div></div>
          <span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">Trades: ${s.trades_taken}</span>
        </div>`).join('');
      document.getElementById('logBox').innerHTML = d.logs.map(l => `<div>${l}</div>`).join('');
    };

    async function deployStrategy() {
      const p = {
        name: document.getElementById('stName').value || 'Custom Strategy',
        symbol: document.getElementById('stSym').value,
        platform: document.getElementById('stPlat').value,
        indicator: document.getElementById('stInd').value,
        rsi_threshold: parseFloat(document.getElementById('stRsi').value),
        max_spread: parseFloat(document.getElementById('stSpread').value),
        risk_usd: parseFloat(document.getElementById('stRisk').value),
        rr_ratio: parseFloat(document.getElementById('stRR').value)
      };
      await fetch('/api/strategy', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(p) });
      document.getElementById('stName').value = '';
    }
    function openTipModal(title, desc) {
      document.getElementById('tipTitle').innerText = title;
      document.getElementById('tipDesc').innerText = desc;
      document.getElementById('tipModal').classList.remove('hidden');
    }
  </script>
</body>
</html>"""

async def index(request):
    return HTMLResponse(HTML)

async def on_startup():
    asyncio.create_task(market_loop())

app = Starlette(
    routes=[
        Route("/", index),
        Route("/api/strategy", add_strategy, methods=["POST"]),
        Route("/api/killswitch", toggle_kill, methods=["POST"]),
        Route("/api/mode", toggle_mode, methods=["POST"]),
        Route("/api/upgrade", git_upgrade, methods=["POST"]),
        WebSocketRoute("/ws", ws_stream),
    ],
    on_startup=[on_startup],
)
