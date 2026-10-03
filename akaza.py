import re
import random
import unicodedata
from telethon import TelegramClient, events

# ================= TELEGRAM CONFIG =================
API_ID = 37846916
API_HASH = "4e3784d4d626f589b50158e92cc93d5d"
SESSION_NAME = "akaza_user"

SOURCE_CHAT = "@predictor7700"          
TARGET_CHAT = "@akazagodmodeelite"      

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ================= STATE & STATS =================
current_prediction = {
    "period": None,
    "signal": None,
    "number": None,
    "confidence": 92
}

history_results = []
last_processed_period = None
total_wins = 124
current_streak = 3

# ================= TEXT MESSAGE GENERATOR =================
def format_prediction_card():
    period_val = f"#{current_prediction['period']}" if current_prediction['period'] else "--"
    sig_val = (current_prediction["signal"] or "--").upper()
    num_val = current_prediction["number"] or "--"
    conf_val = current_prediction.get("confidence", 92)

    table_lines = "┌───┬────────┬────────┬────────┬────────┐\n"
    table_lines += "│ # │ PERIOD │ SIGNAL │ NUMBER │ RESULT │\n"
    table_lines += "├───┼────────┼────────┼────────┼────────┤\n"
    
    recent_history = history_results[-10:]
    if not recent_history:
        table_lines += "│ - │   --   │   --   │   --   │   --   │\n"
    else:
        for idx, item in enumerate(recent_history):
            r_num = str(idx + 1).center(3)
            r_p = str(item.get("period", "--"))[:6].center(8)
            r_s = str(item.get("signal", "--"))[:6].center(8)
            r_n = str(item.get("number", "--"))[:6].center(8)
            r_res = str(item.get("result", "--"))[:6].center(8)
            table_lines += f"│{r_num}│{r_p}│{r_s}│{r_n}│{r_res}│\n"
        
    table_lines += "└───┴────────┴────────┴────────┴────────┘"

    msg = (
        "╔════════════════════════════════════╗\n"
        "⚡       AKAZA ∞ AUTO PREDICTION       ⚡\n"
        "╚════════════════════════════════════╝\n\n"
        f"🎯 PERIOD  : {period_val}\n"
        f"🔮 SIGNAL  : {sig_val}\n"
        f"🔢 NUMBER  : {num_val}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 CONFIDENCE : {conf_val}%\n"
        f"🏆 WINS : {total_wins}  |  🔥 STREAK : {current_streak}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📋 PREVIOUS 10 RESULTS:\n"
        f"```\n{table_lines}```\n\n"
        "contact : @Gara00077"
    )
    return msg

# ================= MESSAGE PROCESSOR =================
async def process_incoming(message):
    global current_prediction, history_results, last_processed_period, total_wins, current_streak

    # Extract text from all possible Telethon attributes
    text = ""
    if hasattr(message, 'message') and message.message:
        text = message.message
    elif hasattr(message, 'text') and message.text:
        text = message.text

    if not text:
        return

    # Normalize stylized italic/bold/gothic fonts into plain text
    clean_text = unicodedata.normalize('NFKD', text)
    clean_upper = clean_text.upper()

    print(f"\n[INCOMING LOG]:\n{clean_text}\n")

    # 1. PREDICTION EXTRACTION (Period + Signal)
    # Check if text has any 3 or 4 digit period
    p_match = re.search(r'PERIOD[^\d\n]*\(?\s*(\d{2,4})\s*\)?', clean_text, re.IGNORECASE)
    if not p_match:
        p_match = re.search(r'#?(\d{3,4})', clean_text)

    # Check for keywords
    s_match = re.search(r'(BIG|SMALL|GREEN|RED|VIOLET)', clean_upper)
    n_match = re.search(r'NUMBER[^\d\n]*(\d+\s*[\/\-]\s*\d+|\d+)', clean_text, re.IGNORECASE)

    # Make sure this isn't the result card (LOSS NUM:9 BIG)
    is_result_pattern = bool(re.search(r'(RESULT\s*=>|NUM\s*:\s*\d+|❌\s*LOSS|LOSS\s*=>)', clean_text, re.IGNORECASE))

    # TRIGGER PREDICTION IF FOUND
    if p_match and s_match and not is_result_pattern:
        period = p_match.group(1).lstrip("0") or p_match.group(1)
        signal = s_match.group(1)
        number = n_match.group(1).strip() if n_match else "--"

        if period != last_processed_period:
            last_processed_period = period
            current_prediction["period"] = period
            current_prediction["signal"] = signal
            current_prediction["number"] = number
            current_prediction["confidence"] = random.randint(86, 96)

            print(f"[FOUND PREDICTION] Period: #{period} | Signal: {signal}")
            card_msg = format_prediction_card()
            try:
                await client.send_message(TARGET_CHAT, card_msg)
                print("[SUCCESS] Sent Prediction Text Card to Target Channel!")
            except Exception as e:
                print(f"[ERROR SENDING CARD]: {e}")
        return

    # 2. RESULT EXTRACTION (WIN / LOSS)
    is_win = bool(re.search(r'(\bWIN\b|✅\s*WIN)', clean_text, re.IGNORECASE)) and "WINGO" not in clean_upper
    is_loss = bool(re.search(r'(\bLOSS\b|\bLOSE\b|❌\s*LOSS)', clean_text, re.IGNORECASE))

    if is_win or is_loss:
        res_label = "WIN" if is_win else "LOSS"
        res_p = re.search(r'#?(\d{3,4})', clean_text)
        res_period = res_p.group(1).lstrip("0") if res_p else (current_prediction["period"] or "--")

        if is_win:
            total_wins += 1
            current_streak += 1
            res_msg = f"🥳🥳🥳 **WIN WIN WIN!!** 🎉🎉🎉\n\n🎯 Period: #{res_period}\n\ncontact : @Gara00077"
        else:
            current_streak = 0
            res_msg = f"🥺🥺🥺 **LOSS NEXT WILL RECOVER** 💔💔\n\n🎯 Period: #{res_period}\n\ncontact : @Gara00077"

        history_results.append({
            "period": f"#{res_period}",
            "signal": current_prediction["signal"] or "--",
            "number": current_prediction["number"] or "--",
            "result": res_label
        })

        if len(history_results) > 10:
            history_results = history_results[-10:]

        await client.send_message(TARGET_CHAT, res_msg)
        print(f"[SUCCESS] Sent {res_label} message to Target!")
        return

# Telethon listeners for both new and edited posts
@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def on_new(event):
    await process_incoming(event.message)

@client.on(events.MessageEdited(chats=SOURCE_CHAT))
async def on_edit(event):
    await process_incoming(event.message)

print("[-] Bot listening to source channel...")
client.start()
client.run_until_disconnected()
