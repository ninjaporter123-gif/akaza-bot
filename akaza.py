import os
import re
import time
import random
import asyncio
import threading
import unicodedata
from flask import Flask, jsonify, request
from flask_cors import CORS
from telethon import TelegramClient, events
from telethon.sessions import MemorySession

# TELEGRAM CONFIG
API_ID = 37846916
API_HASH = "4e3784d4d626f589b50158e92cc93d5d"
BOT_TOKEN = "8905199041:AAFSlBBlX73hpyk2M2iAyD2w7IvIF8mBTTQ"
SOURCE_CHAT = "@predictor7700"

data_lock = threading.Lock()
ADMIN_PASS = "niranjan123"

USER_TOKENS = {
    "NIRANJAN_VIP": time.time() + (365 * 86400 * 5)
}

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

server = Flask(__name__)
CORS(server)

@server.route('/')
def home():
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error loading index.html: {e}"

@server.route('/api/live')
def api_live():
    token = request.args.get('token', '').strip()
    current_time = time.time()
    with data_lock:
        if not token or token not in USER_TOKENS:
            return jsonify({"access": False, "msg": "Invalid Token!"})
        expiry = USER_TOKENS[token]
        if current_time > expiry:
            return jsonify({"access": False, "msg": "Token Expired!"})
        resp = dict(live_data)
        resp["access"] = True
        resp["remaining_seconds"] = int(expiry - current_time)
        return jsonify(resp)

@server.route('/api/admin/tokens')
def get_tokens():
    pwd = request.args.get('pass')
    if pwd != ADMIN_PASS:
        return jsonify({"status": "error", "msg": "Unauthorized"}), 403
    current_time = time.time()
    tokens_list = []
    with data_lock:
        for t, exp in USER_TOKENS.items():
            rem = max(0, int(exp - current_time))
            tokens_list.append({"token": t, "remaining_seconds": rem})
    return jsonify({"status": "success", "tokens": tokens_list})

@server.route('/api/admin/add_token', methods=['POST'])
def add_token():
    data = request.get_json() or {}
    if data.get('pass') != ADMIN_PASS:
        return jsonify({"status": "error", "msg": "Unauthorized"}), 403
    token_name = data.get('token', '').strip()
    duration = float(data.get('duration', 1))
    dur_type = data.get('type', 'hours')
    multiplier = 60 if dur_type == "minutes" else (3600 if dur_type == "hours" else 86400)
    expiry = time.time() + (duration * multiplier)
    with data_lock:
        USER_TOKENS[token_name] = expiry
    return jsonify({"status": "success", "token": token_name})

@server.route('/api/admin/del_token', methods=['POST'])
def del_token():
    data = request.get_json() or {}
    if data.get('pass') != ADMIN_PASS:
        return jsonify({"status": "error", "msg": "Unauthorized"}), 403
    token_name = data.get('token', '').strip()
    with data_lock:
        if token_name in USER_TOKENS:
            del USER_TOKENS[token_name]
    return jsonify({"status": "success"})

def run_telethon():
    while True:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            client = TelegramClient(MemorySession(), API_ID, API_HASH)

            async def main():
                global last_processed_period
                await client.start(bot_token=BOT_TOKEN)
                print("[+] Telegram connected to source channel!")

                @client.on(events.NewMessage(chats=SOURCE_CHAT))
                @client.on(events.MessageEdited(chats=SOURCE_CHAT))
                async def handler(event):
                    global last_processed_period
                    text = event.message.message or event.message.text or ""
                    if not text:
                        return
                    clean_text = unicodedata.normalize('NFKD', text)
                    clean_upper = clean_text.upper()

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
                            print(f"[PREDICTION] Period: #{period} | Signal: {signal}")
                        return

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
        except Exception as e:
            print(f"[!] Reconnecting in 5s: {e}")
            time.sleep(5)

if __name__ == "__main__":
    t = threading.Thread(target=run_telethon, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port, debug=False)
    
