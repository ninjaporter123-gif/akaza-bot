import os
import re
import random
import asyncio
import threading
import unicodedata
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from telethon import TelegramClient, events

# ================= TELEGRAM CONFIG =================
API_ID = 37846916
API_HASH = "4e3784d4d626f589b50158e92cc93d5d"
BOT_TOKEN = "8905199041:AAFSlBBlX73hpyk2M2iAyD2w7IvIF8mBTTQ"

SOURCE_CHAT = "@predictor7700"

# ================= SHARED DATA =================
data_lock = threading.Lock()

live_data = {
    "period": "WAIT",
    "signal": "WAITING",
    "number": "--",
    "confidence": 92,
    "wins": 124,
    "streak": 3,
    "history": []
}

last_processed_period = None

# ================= EMBEDDED HTML VIEWER =================
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AKAZA AUTO PREDICTION</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #030712;
            --panel: rgba(8, 17, 36, 0.92);
            --neon-blue: #00e5ff;
            --neon-pink: #ff007f;
            --neon-green: #00ff88;
            --neon-red: #ff334b;
            --gold: #ffbe0b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: radial-gradient(circle at 50% 20%, #0d2249 0%, var(--bg) 90%);
            color: #fff;
            font-family: 'Rajdhani', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 16px;
        }

        .dashboard {
            width: 100%;
            max-width: 440px;
            background: var(--panel);
            border: 2px solid var(--neon-blue);
            border-radius: 22px;
            box-shadow: 0 0 35px rgba(0, 229, 255, 0.35), inset 0 0 20px rgba(0, 229, 255, 0.12);
            padding: 22px;
            backdrop-filter: blur(14px);
            text-align: center;
        }

        .brand-header h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 21px;
            color: #fff;
            text-shadow: 0 0 12px var(--neon-blue);
            letter-spacing: 2px;
        }

        .brand-tag {
            color: var(--neon-pink);
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-top: 4px;
            margin-bottom: 20px;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }

        .box {
            background: rgba(3, 8, 20, 0.95);
            border: 1px solid rgba(0, 229, 255, 0.4);
            border-radius: 14px;
            padding: 12px 6px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.6);
            transition: all 0.3s ease;
        }

        .box-label {
            font-size: 11px;
            color: #8da4c4;
            font-weight: bold;
            margin-bottom: 6px;
            letter-spacing: 1px;
        }

        .box-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 18px;
            color: #fff;
            font-weight: 900;
        }

        .sig-green { color: var(--neon-green) !important; text-shadow: 0 0 12px var(--neon-green); }
        .sig-red { color: var(--neon-red) !important; text-shadow: 0 0 12px var(--neon-red); }
        .sig-blue { color: var(--neon-blue) !important; text-shadow: 0 0 12px var(--neon-blue); }

        .stats-bar {
            display: flex;
            justify-content: space-around;
            background: rgba(0, 229, 255, 0.08);
            border: 1px solid rgba(0, 229, 255, 0.25);
            border-radius: 12px;
            padding: 10px 6px;
            margin-bottom: 20px;
            font-size: 14px;
            font-weight: 700;
        }

        .history-card {
            background: rgba(2, 6, 16, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            overflow: hidden;
            margin-bottom: 18px;
        }

        .history-title {
            background: rgba(0, 229, 255, 0.14);
            padding: 8px;
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 2px;
            color: var(--neon-blue);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        th, td {
            padding: 8px 4px;
            text-align: center;
        }

        th { 
            color: #8198b5; 
            border-bottom: 1px solid rgba(255, 255, 255, 0.08); 
        }

        tr:nth-child(even) { background: rgba(255, 255, 255, 0.02); }

        .tag-win { 
            color: var(--neon-green); 
            font-weight: 900; 
            text-shadow: 0 0 8px rgba(0, 255, 136, 0.5); 
        }

        .tag-loss { 
            color: var(--neon-red); 
            font-weight: 900; 
            text-shadow: 0 0 8px rgba(255, 51, 75, 0.5); 
        }

        .footer-note {
            font-size: 13px;
            color: #7b94b2;
        }

        .footer-note a {
            color: var(--neon-blue);
            text-decoration: none;
            font-weight: bold;
        }
    </style>
</head>
<body>

<div class="dashboard">
    <div class="brand-header">
        <h1>⚡ AKAZA ∞ AUTO ⚡</h1>
        <div class="brand-tag">REAL-TIME SOURCE VIEWER</div>
    </div>

    <div class="metrics-grid">
        <div class="box">
            <div class="box-label">PERIOD</div>
            <div id="periodBox" class="box-value">#---</div>
        </div>
        <div class="box">
            <div class="box-label">SIGNAL</div>
            <div id="signalBox" class="box-value sig-blue">WAIT</div>
        </div>
        <div class="box">
            <div class="box-label">NUMBER</div>
            <div id="numberBox" class="box-value" style="color: var(--gold);">--</div>
        </div>
    </div>

    <div class="stats-bar">
        <div>CONFIDENCE: <span id="confBox" style="color: var(--neon-blue);">92%</span></div>
        <div>WINS: <span id="winsBox" style="color: var(--neon-green);">124</span></div>
        <div>STREAK: <span id="streakBox" style="color: var(--neon-pink);">3</span></div>
    </div>

    <div class="history-card">
        <div class="history-title">PREVIOUS 10 ROUNDS</div>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>PERIOD</th>
                    <th>SIGNAL</th>
                    <th>NUM</th>
                    <th>RESULT</th>
                </tr>
            </thead>
            <tbody id="historyRows">
                <tr><td colspan="5" style="color: #667e99; padding: 16px;">Connecting to source...</td></tr>
            </tbody>
        </table>
    </div>

    <div class="footer-note">
        LIVE ENGINE | Contact: <a href="https://t.me/Gara00077" target="_blank">@Gara00077</a>
    </div>
</div>

<script>
    async function fetchSourceData() {
        try {
            const res = await fetch('/api/live');
            const data = await res.json();

            document.getElementById('periodBox').innerText = '#' + (data.period || '---');

            const sigEl = document.getElementById('signalBox');
            const sigVal = (data.signal || 'WAIT').toUpperCase();
            sigEl.innerText = sigVal;
            sigEl.className = 'box-value';

            if (sigVal.includes('SMALL') || sigVal.includes('GREEN')) {
                sigEl.classList.add('sig-green');
            } else if (sigVal.includes('BIG') || sigVal.includes('RED')) {
                sigEl.classList.add('sig-red');
            } else {
                sigEl.classList.add('sig-blue');
            }

            document.getElementById('numberBox').innerText = data.number || '--';
            document.getElementById('confBox').innerText = (data.confidence || 92) + '%';
            document.getElementById('winsBox').innerText = data.wins || 0;
            document.getElementById('streakBox').innerText = data.streak || 0;

            if (data.history && data.history.length > 0) {
                let rowsHtml = '';
                data.history.slice(-10).forEach((item, index) => {
                    const resClass = (item.result || '').includes('WIN') ? 'tag-win' : 'tag-loss';
                    rowsHtml += `
                        <tr>
                            <td>${index + 1}</td>
                            <td>#${item.period}</td>
                            <td>${item.signal}</td>
                            <td>${item.number}</td>
                            <td class="${resClass}">${item.result}</td>
                        </tr>
                    `;
                });
                document.getElementById('historyRows').innerHTML = rowsHtml;
            }
        } catch (err) {
            console.error('Fetch error:', err);
        }
    }

    setInterval(fetchSourceData, 1500);
    fetchSourceData();
</script>

</body>
</html>
"""

# ================= FLASK SERVER =================
server = Flask(__name__)
CORS(server)

@server.route('/')
def home():
    return render_template_string(HTML_CODE)

@server.route('/api/live')
def api_live():
    with data_lock:
        return jsonify(live_data)

# ================= TELETHON BACKGROUND THREAD =================
def run_telethon():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = TelegramClient("bot_session", API_ID, API_HASH)

    async def main():
        global last_processed_period

        await client.start(bot_token=BOT_TOKEN)
        print("[+] Telegram Bot connected successfully!")

        @client.on(events.NewMessage(chats=SOURCE_CHAT))
        @client.on(events.MessageEdited(chats=SOURCE_CHAT))
        async def handler(event):
            global last_processed_period

            text = event.message.message or event.message.text or ""
            if not text:
                return

            clean_text = unicodedata.normalize('NFKD', text)
            clean_upper = clean_text.upper()

            # Prediction
            p_match = re.search(r'PERIOD[^\d\n]*\(?\s*(\d{2,4})\s*\)?', clean_text, re.IGNORECASE) or re.search(r'#?(\d{3,4})', clean_text)
            s_match = re.search(r'(BIG|SMALL|GREEN|RED|VIOLET)', clean_upper)
            n_match = re.search(r'NUMBER[^\d\n]*(\d+\s*[\/\-]\s*\d+|\d+)', clean_text, re.IGNORECASE)
            is_result = bool(re.search(r'(RESULT\s*=>|NUM\s*:\s*\d+|❌\s*LOSS|LOSS\s*=>)', clean_text, re.IGNORECASE))

            if p_match and s_match and not is_result:
                period = p_match.group(1).lstrip("0") or p_match.group(1)
                signal = s_match.group(1)
                number = n_match.group(1).strip() if n_match else "--"

                if period != last_processed_period:
                    last_processed_period = period
                    with data_lock:
                        live_data["period"] = period
                        live_data["signal"] = signal
                        live_data["number"] = number
                        live_data["confidence"] = random.randint(86, 96)
                    print(f"[HTML UPDATED] Period: #{period} | Signal: {signal}")
                return

            # Result
            is_win = bool(re.search(r'(\bWIN\b|✅\s*WIN)', clean_text, re.IGNORECASE)) and "WINGO" not in clean_upper
            is_loss = bool(re.search(r'(\bLOSS\b|\bLOSE\b|❌\s*LOSS)', clean_text, re.IGNORECASE))

            if is_win or is_loss:
                res_label = "WIN" if is_win else "LOSS"
                res_p = re.search(r'#?(\d{3,4})', clean_text)
                res_period = res_p.group(1).lstrip("0") if res_p else live_data["period"]

                with data_lock:
                    if is_win:
                        live_data["wins"] += 1
                        live_data["streak"] += 1
                    else:
                        live_data["streak"] = 0

                    live_data["history"].append({
                        "period": res_period,
                        "signal": live_data["signal"],
                        "number": live_data["number"],
                        "result": res_label
                    })
                    if len(live_data["history"]) > 10:
                        live_data["history"] = live_data["history"][-10:]

                print(f"[RESULT] {res_label} for Period #{res_period}")

        await client.run_until_disconnected()

    loop.run_until_complete(main())

# ================= START MAIN APP =================
if __name__ == "__main__":
    # Start Telegram background listener
    t = threading.Thread(target=run_telethon, daemon=True)
    t.start()

    # Flask binds directly to Railway assigned PORT
    port = int(os.environ.get("PORT", 8080))
    print(f"[-] Starting Flask server on 0.0.0.0:{port}...")
    server.run(host="0.0.0.0", port=port)
