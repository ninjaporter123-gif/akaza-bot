import os
import re
import urllib.request
import unicodedata
from telethon import TelegramClient, events
from PIL import Image, ImageDraw, ImageFont

# ================= TELEGRAM CONFIG =================
API_ID = 37846916
API_HASH = "4e3784d4d626f589b50158e92cc93d5d"
SESSION_NAME = "akaza_user"

SOURCE_CHAT = "@predictor7700"          
TARGET_CHAT = "@akazagodmodeelite"      

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ================= FONT AUTO-SETUP =================
# Periya bold font Render server-la download aagidum (Tiny font problem fix)
FONT_FILE = "Roboto-Bold.ttf"
if not os.path.exists(FONT_FILE):
    try:
        font_url = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Bold.ttf"
        urllib.request.urlretrieve(font_url, FONT_FILE)
        print("[+] Custom Bold font downloaded successfully!")
    except Exception as e:
        print(f"[!] Font download error: {e}")

# ================= STATE & HISTORY =================
current_prediction = {
    "period": None,
    "signal": None,
    "number": None
}

history_results = []
last_processed_period = None

# ================= IMAGE GENERATOR =================
def generate_prediction_card():
    if not os.path.exists("template.png"):
        print("[!] ERROR: template.png file kanom!")
        return None

    try:
        base_img = Image.open("template.png").convert("RGB")
        draw = ImageDraw.Draw(base_img)
        
        # Load big and clear font
        if os.path.exists(FONT_FILE):
            font_top = ImageFont.truetype(FONT_FILE, 45)      # Top prediction (Bold & Big)
            font_table = ImageFont.truetype(FONT_FILE, 26)    # Table rows
        else:
            font_top = ImageFont.load_default()
            font_table = ImageFont.load_default()

        # --- 1. TOP CURRENT PREDICTION BOXES ---
        period_val = f"#{current_prediction['period']}" if current_prediction['period'] else "--"
        sig_val = (current_prediction["signal"] or "--").upper()
        num_val = current_prediction["number"] or "--"

        if "GREEN" in sig_val or "SMALL" in sig_val:
            sig_color = (0, 255, 128)      # Bright Neon Green
        elif "RED" in sig_val or "BIG" in sig_val:
            sig_color = (255, 55, 75)       # Bright Neon Red
        else:
            sig_color = (0, 220, 255)       # Cyan Blue

        # Clear previous dummy boxes
        draw.rectangle([(150, 412), (355, 470)], fill=(7, 14, 27))
        draw.rectangle([(400, 412), (600, 470)], fill=(7, 14, 27))
        draw.rectangle([(648, 412), (855, 470)], fill=(7, 14, 27))

        # Center draw helper function
        def draw_centered(box_cx, box_cy, text, color, font_obj):
            try:
                bbox = draw.textbbox((0, 0), text, font=font_obj)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                draw.text((box_cx - (w / 2), box_cy - (h / 2) - 4), text, fill=color, font=font_obj)
            except Exception:
                draw.text((box_cx - 30, box_cy - 15), text, fill=color, font=font_obj)

        # Draw Big & Clear Top Predictions
        draw_centered(252, 441, period_val, (255, 255, 255), font_top)
        draw_centered(500, 441, sig_val, sig_color, font_top)
        draw_centered(751, 441, num_val, (255, 215, 0), font_top)

        # --- 2. PREVIOUS 10 RESULTS (TABLE FILL) ---
        row_start_y = 660
        row_height = 28
        
        # Clear table area
        draw.rectangle([(145, 650), (875, 940)], fill=(8, 16, 32))

        for idx, item in enumerate(history_results[-10:]):
            curr_y = row_start_y + (idx * row_height)
            
            # Index #
            draw.text((165, curr_y), str(idx + 1), fill=(180, 190, 210), font=font_table)
            
            # Period
            draw.text((245, curr_y), str(item.get("period", "--")), fill=(255, 255, 255), font=font_table)
            
            # Signal
            row_sig = str(item.get("signal", "--"))
            row_col = (0, 255, 128) if "GREEN" in row_sig or "SMALL" in row_sig else (255, 60, 80)
            draw.text((430, curr_y), row_sig, fill=row_col, font=font_table)
            
            # Number
            draw.text((615, curr_y), str(item.get("number", "--")), fill=(255, 215, 0), font=font_table)
            
            # Result (WIN / LOSS)
            res_val = str(item.get("result", "--"))
            res_col = (0, 255, 128) if "WIN" in res_val else (255, 60, 80)
            draw.text((760, curr_y), res_val, fill=res_col, font=font_table)

        out_file = "send_prediction.jpg"
        base_img.save(out_file, "JPEG", quality=95)
        return out_file
    except Exception as img_err:
        print(f"[!] Error creating card: {img_err}")
        return None

# ================= MESSAGE LISTENER =================
@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def message_handler(event):
    global current_prediction, history_results, last_processed_period
    raw_text = event.raw_text
    if not raw_text:
        return

    clean_text = unicodedata.normalize('NFKD', raw_text)

    # 1. NEW PREDICTION SIGNAL CHECK
    p_match = re.search(r'PERIOD.*?\(?\s*(\d+)\s*\)?', clean_text, re.IGNORECASE)
    s_match = re.search(r'SIGNAL.*?(BIG|SMALL|GREEN|RED|VIOLET)', clean_text, re.IGNORECASE)
    if not s_match:
        s_match = re.search(r'(BIG|SMALL|GREEN|RED|VIOLET)', clean_text, re.IGNORECASE)

    n_match = re.search(r'NUMBER.*?(\d+\s*[\/\-]\s*\d+|\d+)', clean_text, re.IGNORECASE)

    is_prediction_msg = bool(p_match and s_match and ("SIGNAL" in clean_text.upper() or "WINGO" in clean_text.upper()))

    if is_prediction_msg:
        period = p_match.group(1)
        signal = s_match.group(1).upper()
        number = n_match.group(1).strip() if n_match else ""

        if period != last_processed_period:
            last_processed_period = period
            current_prediction["period"] = period
            current_prediction["signal"] = signal
            current_prediction["number"] = number

            print(f"[+] Prediction match: #{period} | {signal} | {number}")
            
            img_path = generate_prediction_card()
            caption_text = "contact : @Gara00077"

            try:
                if img_path and os.path.exists(img_path):
                    await client.send_file(TARGET_CHAT, img_path, caption=caption_text)
                    print("[SUCCESS] Big text prediction card sent!")
                else:
                    await client.send_message(TARGET_CHAT, caption_text)
            except Exception as send_err:
                print(f"[!] Send error: {send_err}")
        return

    # 2. WIN / LOSS RESULTS CHECK
    is_win = bool(re.search(r'(^|\s|✅)\s*WIN(\s|!|$)', clean_text, re.IGNORECASE))
    is_loss = bool(re.search(r'(^|\s|❌)\s*LOSS(\s|!|$)|LOSE', clean_text, re.IGNORECASE))

    if is_win or is_loss:
        res_label = "WIN" if is_win else "LOSS"
        res_p = re.search(r'PERIOD.*?#?(\d+)', clean_text, re.IGNORECASE)
        res_period = res_p.group(1) if res_p else (current_prediction["period"] or "--")

        history_results.append({
            "period": res_period,
            "signal": current_prediction["signal"] or "--",
            "number": current_prediction["number"] or "--",
            "result": res_label
        })

        if len(history_results) > 10:
            history_results = history_results[-10:]

        if is_win:
            res_msg = f"🥳🥳🥳 **WIN WIN WIN!!** 🎉🎉🎉\n\n🎯 Period: #{res_period}\n\ncontact : @Gara00077"
        else:
            res_msg = f"🥺🥺🥺 **LOSS NEXT WILL RECOVER** 💔💔\n\n🎯 Period: #{res_period}\n\ncontact : @Gara00077"

        await client.send_message(TARGET_CHAT, res_msg)
        print(f"[+] Result handled: {res_label} for Period #{res_period}")
        return

print("[-] AKAZA AUTO Bot is Running...")
client.start()
client.run_until_disconnected()
