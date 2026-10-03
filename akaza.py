import os
import re
import time
import random
import asyncio
import threading
import unicodedata
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from telethon import TelegramClient, events

# ================= TELEGRAM CONFIG =================
API_ID = 37846916
API_HASH = "4e3784d4d626f589b50158e92cc93d5d"
BOT_TOKEN = "8905199041:AAFSlBBlX73hpyk2M2iAyD2w7IvIF8mBTTQ"

SOURCE_CHAT = "@predictor7700"

# ================= SHARED DATA & TOKENS =================
data_lock = threading.Lock()

# Token format: { "TOKEN_KEY": expiry_epoch_timestamp }
# Default 1 Master Lifetime Key:
USER_TOKENS = {
    "NIRANJAN_VIP": time.time() + (365 * 86400 * 5)
}

ADMIN_PASS = "niranjan123"

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

# ================= EMBEDDED HTML VIEWER + ADMIN =================
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AKAZA AUTO PREDICTION VIP</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #030712;
            --panel: rgba(8, 17, 36, 0.94);
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
            position: relative;
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
            margin-bottom: 15px;
        }

        .validity-strip {
            background: rgba(0, 229, 255, 0.08);
            border: 1px solid rgba(0, 229, 255, 0.3);
            border-radius: 12px;
            padding: 6px 12px;
            font-size: 13px;
            font-weight: bold;
            color: var(--gold);
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
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

        th, td { padding: 8px 4px; text-align: center; }
        th { color: #8198b5; border-bottom: 1px solid rgba(255, 255, 255, 0.08); }
        tr:nth-child(even) { background: rgba(255, 255, 255, 0.02); }

        .tag-win { color: var(--neon-green); font-weight: 900; }
        .tag-loss { color: var(--neon-red); font-weight: 900; }

        .footer-note {
            font-size: 13px;
            color: #7b94b2;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .admin-link {
            color: #8da4c4;
            font-size: 12px;
            text-decoration: none;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.2);
            padding: 3px 8px;
            border-radius: 6px;
        }
        .admin-link:hover { color: var(--neon-blue); border-color: var(--neon-blue); }

        /* MODALS */
        .overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(2, 6, 16, 0.95);
            backdrop-filter: blur(10px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 999;
            padding: 15px;
        }

        .modal-box {
            width: 100%;
            max-width: 380px;
            background: #091224;
            border: 2px solid var(--neon-blue);
            border-radius: 18px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 0 30px rgba(0, 229, 255, 0.4);
        }

        .cyber-input {
            width: 100%;
            background: rgba(3, 8, 20, 0.9);
            border: 1px solid var(--neon-blue);
            color: #fff;
            padding: 12px;
            border-radius: 8px;
            font-family: 'Rajdhani', sans-serif;
            font-size: 16px;
            margin: 12px 0;
            outline: none;
            text-align: center;
        }

        .cyber-btn {
            background: linear-gradient(45deg, var(--neon-blue), #0077ff);
            color: #fff;
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            font-weight: bold;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            margin-top: 6px;
        }
        .cyber-btn:hover { opacity: 0.9; }

        .admin-token-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255,255,255,0.04);
            padding: 6px 10px;
            margin: 6px 0;
            border-radius: 6px;
            font-size: 13px;
        }
    </style>
</head>
<body>

<!-- USER TOKEN LOGIN MODAL -->
<div id="loginModal" class="overlay" style="display: flex;">
    <div class="modal-box">
        <h2 style="font-family: 'Orbitron'; font-size: 18px; color: var(--neon-blue); margin-bottom: 8px;">VIP AUTHENTICATION</h2>
        <p style="font-size: 13px; color: #8da4c4;">Access Token is required to view live predictions.</p>
        <input type="text" id="tokenInput" class="cyber-input" placeholder="ENTER ACCESS TOKEN">
        <button onclick="submitToken()" class="cyber-btn">UNLOCK DASHBOARD</button>
        <p id="loginError" style="color: var(--neon-red); font-size: 13px; margin-top: 10px; display: none;"></p>
        <p style="font-size: 12px; color: #667e99; margin-top: 15px;">Need Token? Contact: <a href="https://t.me/Gara00077" target="_blank" style="color: var(--neon-blue);">@Gara00077</a></p>
    </div>
</div>

<!-- ADMIN MODAL -->
<div id="adminModal" class="overlay" style="display: none;">
    <div class="modal-box" style="max-width: 440px; text-align: left;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h2 style="font-family: 'Orbitron'; font-size: 16px; color: var(--neon-pink);">ADMIN CONTROL PANEL</h2>
            <button onclick="closeAdmin()" style="background:none; border:none; color:#fff; font-size:18px; cursor:pointer;">✖</button>
        </div>

        <div style="margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px;">
            <label style="font-size: 12px; color: #8da4c4;">GENERATE NEW TOKEN</label>
            <input type="text" id="newTokenName" class="cyber-input" placeholder="Token Name (e.g. VIP_USER1)" style="text-align: left; padding: 8px 12px;">
            
            <div style="display: flex; gap: 8px;">
                <input type="number" id="newDuration" class="cyber-input" placeholder="Duration" style="width: 50%; text-align: center; padding: 8px;">
                <select id="durationType" class="cyber-input" style="width: 50%; padding: 8px;">
                    <option value="minutes">Minutes</option>
                    <option value="hours" selected>Hours</option>
                    <option value="days">Days</option>
                </select>
            </div>
            <button onclick="createToken()" class="cyber-btn" style="background: linear-gradient(45deg, var(--neon-pink), #ff0055); margin-top: 4px;">CREATE TOKEN</button>
        </div>

        <div>
            <label style="font-size: 12px; color: #8da4c4;">ACTIVE TOKENS</label>
            <div id="adminTokenList" style="max-height: 180px; overflow-y: auto; margin-top: 8px;"></div>
        </div>
    </div>
</div>

<!-- MAIN DASHBOARD -->
<div class="dashboard">
    <div class="brand-header">
        <h1>⚡ AKAZA ∞ AUTO ⚡</h1>
        <div class="brand-tag">VIP REAL-TIME ENGINE</div>
    </div>

    <div class="validity-strip">
        <span>ACCESS: <span id="tokenStatusText" style="color: var(--neon-green);">ACTIVE</span></span>
        <span>EXPIRES: <span id="timeRemainingText">--:--:--</span></span>
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
        <div>ACCURACY: <span id="confBox" style="color: var(--neon-blue);">92%</span></div>
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
                <tr><td colspan="5" style="color: #667e99; padding: 16px;">Connecting to secure source...</td></tr>
            </tbody>
        </table>
    </div>

    <div class="footer-note">
        <span>VIP Access | <a href="https://t.me/Gara00077" target="_blank" style="color: var(--neon-blue); text-decoration: none;">@Gara00077</a></span>
        <a class="admin-link" onclick="openAdminPrompt()">⚙️ Admin</a>
    </div>
</div>

<script>
    let activeToken = localStorage.getItem('akaza_user_token') || '';
    let adminAuthToken = '';

    function submitToken() {
        const val = document.getElementById('tokenInput').value.trim();
        if (!val) return;
        activeToken = val;
        localStorage.setItem('akaza_user_token', activeToken);
        fetchSourceData();
    }

    function formatTime(seconds) {
        if (seconds <= 0) return "EXPIRED";
        const d = Math.floor(seconds / (3600*24));
        const h = Math.floor((seconds % (3600*24)) / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = seconds % 60;
        if (d > 0) return `${d}d ${h}h ${m}m`;
        return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    }

    async function fetchSourceData() {
        if (!activeToken) {
            document.getElementById('loginModal').style.display = 'flex';
            return;
        }

        try {
            const res = await fetch(`/api/live?token=${encodeURIComponent(activeToken)}`);
            const data = await res.json();

            if (!data.access) {
                document.getElementById('loginModal').style.display = 'flex';
                document.getElementById('loginError').style.display = 'block';
                document.getElementById('loginError').innerText = data.msg || 'Invalid or Expired Token';
                return;
            }

            document.getElementById('loginModal').style.display = 'none';
            document.getElementById('timeRemainingText').innerText = formatTime(data.remaining_seconds);

            // Period
            document.getElementById('periodBox').innerText = '#' + (data.period || '---');

            // Signal
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

            // Stats
            document.getElementById('numberBox').innerText = data.number || '--';
            document.getElementById('confBox').innerText = (data.confidence || 92) + '%';
            document.getElementById('winsBox').innerText = data.wins || 0;
            document.getElementById('streakBox').innerText = data.streak || 0;

            // Table
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

    // ADMIN LOGIC
    function openAdminPrompt() {
        const pass = prompt("ENTER ADMIN PASSWORD:");
        if (pass === "niranjan123") {
            adminAuthToken = pass;
            document.getElementById('adminModal').style.display = 'flex';
            loadAdminTokens();
        } else if (pass !== null) {
            alert("Incorrect Password!");
        }
    }

    function closeAdmin() {
        document.getElementById('adminModal').style.display = 'none';
    }

    async function loadAdminTokens() {
        const res = await fetch(`/api/admin/tokens?pass=${adminAuthToken}`);
        const data = await res.json();
        let html = '';
        data.tokens.forEach(t => {
            html += `
                <div class="admin-token-row">
                    <div>
                        <strong style="color:var(--neon-blue);">${t.token}</strong><br>
                        <span style="font-size:11px; color:#8da4c4;">Rem: ${formatTime(t.remaining_seconds)}</span>
                    </div>
                    <button onclick="deleteToken('${t.token}')" style="background:#ff334b; border:none; color:#fff; border-radius:4px; padding:3px 8px; cursor:pointer;">DEL</button>
                </div>
            `;
        });
        document.getElementById('adminTokenList').innerHTML = html || '<p style="color:#777;font-size:12px;">No tokens</p>';
    }

    async function createToken() {
        const tokenName = document.getElementById('newTokenName').value.trim();
        const duration = parseFloat(document.getElementById('newDuration').value);
        const type = document.getElementById('durationType').value;

        if (!tokenName || isNaN(duration)) {
            alert("Enter valid token name and duration");
            return;
        }

        const res = await fetch(`/api/admin/add_token?pass=${adminAuthToken}&token=${encodeURIComponent(tokenName)}&duration=${duration}&type=${type}`);
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('newTokenName').value = '';
            document.getElementById('newDuration').value = '';
            loadAdminTokens();
        } else {
            alert(data.msg || 'Error adding token');
        }
    }

    async function deleteToken(tok) {
        if (!confirm(`Delete token ${tok}?`)) return;
        await fetch(`/api/admin/del_token?pass=${adminAuthToken}&token=${encodeURIComponent(tok)}`);
        loadAdminTokens();
    }

    setInterval(fetchSourceData, 1500);
    fetchSourceData();
</script>

</body>
</html>
"""

# ================= FLASK SERVER & APIS =================
server = Flask(__name__)
CORS(server)

@server.route('/')
def home():
    return render_template_string(HTML_CODE)

@server.route('/api/live')
def api_live():
    token = request.args.get('token', '').strip()
    current_time = time.time()

    with data_lock:
        if not token or token not in USER_TOKENS:
            return jsonify({"access": False, "msg": "Invalid Token. Access Denied!"})

        expiry = USER_TOKENS[token]
        if current_time > expiry:
            return jsonify({"access": False, "msg": "Your Access Token has Expired!"})

        resp = dict(live_data)
        resp["access"] = True
        resp["remaining_seconds"] = int(expiry - current_time)
        return jsonify(resp)

# ADMIN APIS (PASSWORD PROTECTED)
@server.route('/api/admin/tokens')
def get_tokens():
    pwd = request.args.get('pass')
    if pwd != ADMIN_PASS:
        
