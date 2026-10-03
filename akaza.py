import os
import re
import random
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

# ================= FONT SETUP =================
FONT_FILE = "Roboto-Bold.ttf"
if not os.path.exists(FONT_FILE):
    try:
        font_url = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Bold.ttf"
        urllib.request.urlretrieve(font_url, FONT_FILE)
    except Exception as e:
        print(f"[!] Font error: {e}")

# ================= STATE & STATS =================
current_prediction = {
    "period": None,
    "signal": None,
    "number": None,
    "confidence": 88
}

history_results = []
last_processed_period = None
total_wins = 124
current_streak = 3

# ================= IMAGE GENERATOR =================
def generate_prediction_card():
    if not os.path.exists("template.png"):
        print("[!] ERROR: template.png file kanom!")
        return None

    try:
        base_img = Image.open("template.png").convert("RGB")
        draw = ImageDraw.Draw(base_img)
        
        # Load fonts
        if os.path.exists(FONT_FILE):
            font_top = ImageFont.truetype(FONT_FILE, 38)
            font_mid = ImageFont.truetype(FONT_FILE, 20)
            font_table = ImageFont.truetype(FONT_FILE, 22)
        else:
            font_top = font_mid = font_table = ImageFont.load_default()

        # --- 1. TOP CURRENT PREDICTION (WHITE COLOR) ---
        period_val = f"#{current_prediction['period']}" if current_prediction['period'] else "--"
        sig_val = (current_prediction["signal"] or "--").upper()
        num_val = current_prediction["number"] or "--"

        # Black background patch over previous dummy boxes
        draw.rectangle([(145, 412), (355, 472)], fill=(7, 14, 27))
        draw.rectangle([(398, 412), (602, 472)], fill=(7, 14, 27))
        draw.rectangle([(645, 412), (855, 472)], fill=(7, 14, 27))

        # Center alignment function
        def draw_centered(box_cx, box_cy, text, color, font_obj):
            try:
                bbox = draw.textbbox((0, 0), text, font=font_obj)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                draw.text((box_cx - (w / 2), box_cy - (h / 2) - 3), text, fill=color, font=font_obj)
            except Exception:
                draw.text((box_cx - 25, box_cy - 10), text, fill=color, font=font_obj)

        # Ellam Pure WHITE colour
        draw_centered(250, 442, period_val, (255, 255, 255), font_top)
        draw_centered(500, 442, sig_val, (255, 255, 255), font_top)
        draw_centered(750, 442, num_val, (255, 255, 255), font_top)

        # --- 2. CONFIDENCE, WINS & STREAK (AUTO PERCENTAGE) ---
        # Patch the middle stats strip
        draw.rectangle([(230, 492), (480, 532)], fill=(9, 18, 36))
        draw.rectangle([(510, 492), (785, 532)], fill=(9, 18, 36))

        conf_str = f"CONFIDENCE: {current_prediction['confidence']}%"
        wins_str = f"WINS: {total_wins}  STREAK: {current_streak}"

        draw_centered(355, 512, conf_str, (0, 220, 255), font_mid)
        draw_centered(647, 512, wins_str, (0, 255, 128), font_mid)

        # --- 3. PREVIOUS RESULTS TABLE (WHITE TEXT & NEAT ALIGNMENT) ---
        # Clean table area
        draw.rectangle([(140, 652), (860, 895)], fill=(7, 14, 27))
        
        row_y = 665
        row_gap = 23

        # Display latest history
        for idx, item in enumerate(history_results[-9:]):
            curr_y = row_y + (idx * row_gap)
            
            # Row index
            draw.text((165, curr_y), str(idx + 1), fill=(200, 210, 225), font=font_table)
            # Period (White)
            draw.text((240, curr_y), str(item.get("period", "--")), fill=(255, 255, 255), font=font_table)
            # Signal (White)
            draw.text((410, curr_y), str(item.get("signal", "--")), fill=(255, 255, 255), font=font_table)
            # Number (White)
            draw.text((585, curr_y), str(item.get("number", "--")), fill=(255, 255, 255), font=font_table)
            # Result (WIN / LOSS)
            res_val = str(item.get("result", "--"))
            res_col = (0, 255, 128) if "WIN" in res_val else (255, 60, 80)
            draw.text((750, curr_y), res_val, fill=res_col, font=font_table)

        out_file = "send_prediction.jpg"
        base_img.save(out_file, "JPEG", quality=95)
        return out_file
    except Exception as img_err:
        print(f"[!] Image create error: {img_err}")
        return None

# ================= MESSAGE LISTENER =================
@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def message_handler(event):
    global current_prediction, history_results, last_processed_period, total_wins, current_streak
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
            # Automatic dynamic confidence (82% to 96%)
            current_prediction["confidence"] = random.randint(82, 96)

            print(f"[+] Prediction: #{period} | {signal} | {number}")
            
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
        return

    # 2. WIN / LOSS RESULTS CHECK
    is_win = bool(re.search(r'(^|\s|✅)\s*WIN(\s|!|$)', clean_text, re.IGNORECASE))
    is_loss = bool(re.search(r'(^|\s|❌)\s*LOSS(\s|!|$)|LOSE', clean_text, re.IGNORECASE))

    if is_win or is_loss:
        res_label = "WIN" if is_win else "LOSS"
        res_p = re.search(r'PERIOD.*?#?(\d+)', clean_text, re.IGNORECASE)
        res_period = res_p.group(1) if res_p else (current_prediction["period"] or "--")

        # Stats update
        if is_win:
            total_wins += 1
            current_streak += 1
        else:
            current_streak = 0

        # Save to previous results table
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
        print(f"[+] Result saved: {res_label} for Period #{res_period}")
        return

print("[-] AKAZA AUTO Bot is Running...")
client.start()
client.run_until_disconnected()
            
