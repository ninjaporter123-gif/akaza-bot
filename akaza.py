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

        # --- 1. TOP CURRENT PREDICTION BOXES ---
        period_val = current_prediction["period"] or "--"
        sig_val = (current_prediction["signal"] or "--").upper()
        num_val = current_prediction["number"] or "--"

        if "GREEN" in sig_val or "SMALL" in sig_val:
            sig_color = (0, 255, 128)
        elif "RED" in sig_val or "BIG" in sig_val:
            sig_color = (255, 60, 80)
        else:
            sig_color = (0, 220, 255)

        # Clear top boxes
        draw.rectangle([(150, 412), (355, 470)], fill=(7, 14, 27))
        draw.rectangle([(400, 412), (600, 470)], fill=(7, 14, 27))
        draw.rectangle([(648, 412), (855, 470)], fill=(7, 14, 27))

        draw.text((215, 428), f"#{period_val}", fill=(255, 255, 255), font=font_top)
        draw.text((465, 428), sig_val, fill=sig_color, font=font_top)
        draw.text((725, 428), num_val, fill=(255, 215, 0), font=font_top)

        # --- 2. PREVIOUS 10 RESULTS (TABLE FILL) ---
        row_start_y = 660
        row_height = 28
        
        draw.rectangle([(145, 650), (875, 940)], fill=(8, 16, 32))

        for idx, item in enumerate(history_results[-10:]):
            curr_y = row_start_y + (idx * row_height)
            draw.text((165, curr_y), str(idx + 1), fill=(180, 190, 210), font=font)
            draw.text((245, curr_y), str(item.get("period", "--")), fill=(255, 255, 255), font=font)
            
            row_sig = str(item.get("signal", "--"))
            row_col = (0, 255, 128) if "GREEN" in row_sig or "SMALL" in row_sig else (255, 60, 80)
            draw.text((430, curr_y), row_sig, fill=row_col, font=font)
            
            draw.text((615, curr_y), str(item.get("number", "--")), fill=(255, 215, 0), font=font)
            
            res_val = str(item.get("result", "--"))
            res_col = (0, 255, 128) if "WIN" in res_val else (255, 60, 80)
            draw.text((760, curr_y), res_val, fill=res_col, font=font)

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

    # ---------------- 1. FIRST CHECK: NEW PREDICTION SIGNAL ----------------
    # Prediction vandhirundha modhalla idhu trigger aaganum
    p_match = re.search(r'PERIOD.*?\(?\s*(\d+)\s*\)?', clean_text, re.IGNORECASE)
    s_match = re.search(r'SIGNAL.*?(BIG|SMALL|GREEN|RED|VIOLET)', clean_text, re.IGNORECASE)
    
    if not s_match:
        # Fallback if SIGNAL emoji format
        s_match = re.search(r'(BIG|SMALL|GREEN|RED|VIOLET)', clean_text, re.IGNORECASE)

    n_match = re.search(r'NUMBER.*?(\d+\s*[\/\-]\s*\d+|\d+)', clean_text, re.IGNORECASE)

    # Idhu Prediction message-ah nu verify panrom (SIGNAL koodave PERIOD irukanum)
    is_prediction_msg = bool(p_match and s_match and ("SIGNAL" in clean_text.upper() or "WINGO" in clean_text.upper()))

    if is_prediction_msg:
        period = p_match.group(1)
        signal = s_match.group(1).upper()
        number = n_match.group(1).strip() if n_match else ""

        # Duplicate round avoid panrom
        if period != last_processed_period:
            last_processed_period = period
            current_prediction["period"] = period
            current_prediction["signal"] = signal
            current_prediction["number"] = number

            print(f"[+] Prediction Match: Period={period} | Signal={signal} | Number={number}")
            
            img_path = generate_prediction_card()
            caption_text = "contact : @Gara00077"

            try:
                if img_path and os.path.exists(img_path):
                    await client.send_file(TARGET_CHAT, img_path, caption=caption_text)
                    print("[SUCCESS] Prediction card sent!")
                else:
                    await client.send_message(TARGET_CHAT, caption_text)
            except Exception as send_err:
                print(f"[!] Send error: {send_err}")
        return  # Prediction process aana apram keezha irukura Win check-ku pogaathu!

    # ---------------- 2. SECOND CHECK: WIN / LOSS RESULT ----------------
    # 'WinGo'-vai ignore panni strictly standalone WIN or LOSS check
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
