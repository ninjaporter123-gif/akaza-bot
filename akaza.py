import os
import re
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

# ================= STATE & HISTORY =================
# Kadaisiya vandha prediction details
current_prediction = {
    "period": None,
    "signal": None,
    "number": None
}

# Previous 10 results store panna list: [{period, signal, number, result}]
history_results = []

# ================= IMAGE GENERATOR =================
def generate_prediction_card():
    if not os.path.exists("template.png"):
        print("[!] ERROR: template.png file kanom!")
        return None

    try:
        base_img = Image.open("template.png").convert("RGB")
        draw = ImageDraw.Draw(base_img)
        
        # Safe font loader
        font = None
        for font_name in ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "arial.ttf"]:
            try:
                font = ImageFont.truetype(font_name, 22)
                font_top = ImageFont.truetype(font_name, 32)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()
            font_top = font

        # --- 1. CURRENT PREDICTION (TOP BOXES) ---
        period_val = current_prediction["period"] or "--"
        sig_val = (current_prediction["signal"] or "--").upper()
        num_val = current_prediction["number"] or "--"

        # Signal color
        if "GREEN" in sig_val or "SMALL" in sig_val:
            sig_color = (0, 255, 128)
        elif "RED" in sig_val or "BIG" in sig_val:
            sig_color = (255, 60, 80)
        else:
            sig_color = (0, 220, 255)

        # Top dummy text cover panra patches
        draw.rectangle([(150, 412), (355, 470)], fill=(7, 14, 27))
        draw.rectangle([(400, 412), (600, 470)], fill=(7, 14, 27))
        draw.rectangle([(648, 412), (855, 470)], fill=(7, 14, 27))

        # Top values draw panrom
        draw.text((215, 428), f"#{period_val}", fill=(255, 255, 255), font=font_top)
        draw.text((465, 428), sig_val, fill=sig_color, font=font_top)
        draw.text((725, 428), num_val, fill=(255, 215, 0), font=font_top)

        # --- 2. PREVIOUS 10 RESULTS (TABLE FILL) ---
        # Table rows starting Y position and row height
        row_start_y = 660
        row_height = 28
        
        # Column X centers: # (170), PERIOD (280), SIGNAL (450), NUMBER (620), RESULT (780)
        # Old table data area cover panna background patch
        draw.rectangle([(145, 650), (875, 940)], fill=(8, 16, 32))

        for idx, item in enumerate(history_results[-10:]):
            curr_y = row_start_y + (idx * row_height)
            
            # Row index
            draw.text((165, curr_y), str(idx + 1), fill=(180, 190, 210), font=font)
            
            # Period
            draw.text((245, curr_y), str(item.get("period", "--")), fill=(255, 255, 255), font=font)
            
            # Signal
            row_sig = str(item.get("signal", "--"))
            row_col = (0, 255, 128) if "GREEN" in row_sig or "SMALL" in row_sig else (255, 60, 80)
            draw.text((430, curr_y), row_sig, fill=row_col, font=font)
            
            # Number
            draw.text((615, curr_y), str(item.get("number", "--")), fill=(255, 215, 0), font=font)
            
            # Result (WIN / LOSS)
            res_val = str(item.get("result", "--"))
            res_col = (0, 255, 128) if "WIN" in res_val else (255, 60, 80)
            draw.text((760, curr_y), res_val, fill=res_col, font=font)

        out_file = "send_prediction.jpg"
        base_img.save(out_file, "JPEG", quality=95)
        return out_file
    except Exception as img_err:
        print(f"[!] Table Image generate panrathula error: {img_err}")
        return None

# ================= MESSAGE LISTENER =================
@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def message_handler(event):
    global current_prediction, history_results
    raw_text = event.raw_text
    if not raw_text:
        return

    clean_text = unicodedata.normalize('NFKD', raw_text)

    # 1. WIN / LOSS CHECK
    if "WIN" in clean_text.upper() or "LOSS" in clean_text.upper() or "LOSE" in clean_text.upper():
        is_win = "WIN" in clean_text.upper()
        res_label = "WIN" if is_win else "LOSS"

        p_match = re.search(r'PERIOD.*?(\d+)', clean_text, re.IGNORECASE)
        res_period = p_match.group(1) if p_match else (current_prediction["period"] or "--")

        # History-la update panrom
        history_results.append({
            "period": res_period,
            "signal": current_prediction["signal"] or "--",
            "number": current_prediction["number"] or "--",
            "result": res_label
        })

        # List romba perusa aagama 10 items mattum maintain panrom
        if len(history_results) > 10:
            history_results = history_results[-10:]

        # Result post send panrom
        if is_win:
            res_msg = f"🥳🥳🥳 **WIN WIN WIN!!** 🎉🎉🎉\n\n🎯 Period: #{res_period}\n\ncontact : @Gara00077"
        else:
            res_msg = f"🥺🥺🥺 **LOSS NEXT WILL RECOVER** 💔💔\n\n🎯 Period: #{res_period}\n\ncontact : @Gara00077"

        await client.send_message(TARGET_CHAT, res_msg)
        print(f"[+] Result handled: {res_label} for Period {res_period}")
        return

    # 2. NEW PREDICTION SIGNAL CHECK
    p_match = re.search(r'PERIOD.*?(\d+)', clean_text, re.IGNORECASE)
    period = p_match.group(1) if p_match else None

    s_match = re.search(r'(BIG|SMALL|GREEN|RED|VIOLET)', clean_text, re.IGNORECASE)
    signal = s_match.group(1).upper() if s_match else None

    n_match = re.search(r'NUMBER.*?([0-9\/\s]+)', clean_text, re.IGNORECASE)
    number = n_match.group(1).strip() if n_match else ""

    if period and signal:
        current_prediction["period"] = period
        current_prediction["signal"] = signal
        current_prediction["number"] = number

        print(f"[+] Prediction updated: Period={period} | Signal={signal} | Number={number}")
        
        img_path = generate_prediction_card()
        caption_text = "contact : @Gara00077"

        try:
            if img_path and os.path.exists(img_path):
                await client.send_file(TARGET_CHAT, img_path, caption=caption_text)
                print("[SUCCESS] Prediction card with updated history table sent!")
            else:
                await client.send_message(TARGET_CHAT, caption_text)
        except Exception as send_err:
            print(f"[!] Send error: {send_err}")

print("[-] AKAZA AUTO Bot is Running...")
client.start()
client.run_until_disconnected()
        
