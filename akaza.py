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

# ================= FONT SETUP =================
# Server-la font illana auto-va clean font download pannidum
FONT_FILE = "arial_bold.ttf"
if not os.path.exists(FONT_FILE):
    try:
        url = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Bold.ttf"
        urllib.request.urlretrieve(url, FONT_FILE)
    except Exception as e:
        print(f"[!] Font download error: {e}")

# ================= IMAGE GENERATOR =================
def generate_prediction_card(period, signal, number):
    if not os.path.exists("template.png"):
        print("[!] ERROR: template.png file kanom!")
        return None

    try:
        base_img = Image.open("template.png").convert("RGB")
        draw = ImageDraw.Draw(base_img)
        
        # Font load panrom
        try:
            font = ImageFont.truetype(FONT_FILE, 36)
        except Exception:
            font = ImageFont.load_default()

        sig_upper = signal.upper()
        if "GREEN" in sig_upper or "SMALL" in sig_upper:
            sig_color = (0, 255, 128)      # Neon Green
        elif "RED" in sig_upper or "BIG" in sig_upper:
            sig_color = (255, 60, 80)       # Neon Red
        else:
            sig_color = (0, 220, 255)       # Cyan Blue

        # Purana dummy text [PERIOD], [SIGNAL], [NUMBER]-ah cover panna dark background patch
        # 1024x1024 exact boxes
        draw.rectangle([(150, 412), (355, 470)], fill=(7, 14, 27))
        draw.rectangle([(400, 412), (600, 470)], fill=(7, 14, 27))
        draw.rectangle([(648, 412), (855, 470)], fill=(7, 14, 27))

        # Center draw helper function
        def draw_centered(box_center_x, box_center_y, text, color):
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                draw.text((box_center_x - (w / 2), box_center_y - (h / 2) - 2), text, fill=color, font=font)
            except Exception:
                draw.text((box_center_x - 30, box_center_y - 15), text, fill=color, font=font)

        # Boxes ulla print panrom
        draw_centered(252, 441, f"#{period}", (255, 255, 255))
        draw_centered(500, 441, sig_upper, sig_color)
        draw_centered(751, 441, str(number) if number else "--", (255, 215, 0))

        out_file = "send_prediction.jpg"
        base_img.save(out_file, "JPEG", quality=95)
        return out_file
    except Exception as img_err:
        print(f"[!] Image create error: {img_err}")
        return None

# ================= MESSAGE LISTENER =================
@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def message_handler(event):
    raw_text = event.raw_text
    if not raw_text:
        return

    clean_text = unicodedata.normalize('NFKD', raw_text)

    # 1. WIN / LOSS RESULTS CHECK
    if "WIN" in clean_text.upper():
        win_period = re.search(r'PERIOD.*?(\d+)', clean_text, re.IGNORECASE)
        p_num = f"#{win_period.group(1)}" if win_period else ""
        win_msg = f"🥳🥳🥳 **WIN WIN WIN!!** 🎉🎉🎉\n\n🎯 Period: {p_num}\n\ncontact : @Gara00077"
        await client.send_message(TARGET_CHAT, win_msg)
        print("[+] Win notification sent!")
        return

    if "LOSS" in clean_text.upper() or "LOSE" in clean_text.upper():
        loss_period = re.search(r'PERIOD.*?(\d+)', clean_text, re.IGNORECASE)
        p_num = f"#{loss_period.group(1)}" if loss_period else ""
        loss_msg = f"🥺🥺🥺 **LOSS NEXT WILL RECOVER** 💔💔\n\n🎯 Period: {p_num}\n\ncontact : @Gara00077"
        await client.send_message(TARGET_CHAT, loss_msg)
        print("[+] Loss notification sent!")
        return

    # 2. PREDICTION SIGNAL PARSING
    p_match = re.search(r'PERIOD.*?(\d+)', clean_text, re.IGNORECASE)
    period = p_match.group(1) if p_match else None

    s_match = re.search(r'(BIG|SMALL|GREEN|RED|VIOLET)', clean_text, re.IGNORECASE)
    signal = s_match.group(1).upper() if s_match else None

    n_match = re.search(r'NUMBER.*?([0-9\/\s]+)', clean_text, re.IGNORECASE)
    number = n_match.group(1).strip() if n_match else ""

    if period and signal:
        print(f"[+] Prediction found: Period={period} | Signal={signal}")
        
        caption_text = "contact : @Gara00077"
        img_path = generate_prediction_card(period, signal, number)
        
        try:
            if img_path and os.path.exists(img_path):
                await client.send_file(TARGET_CHAT, img_path, caption=caption_text)
                print("[SUCCESS] Prediction card sent!")
            else:
                await client.send_message(TARGET_CHAT, caption_text)
        except Exception as send_err:
            print(f"[!] Send error: {send_err}")

print("[-] AKAZA AUTO Bot is Running...")
client.start()
client.run_until_disconnected()
