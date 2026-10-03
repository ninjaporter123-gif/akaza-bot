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

# ================= IMAGE GENERATOR =================
def generate_prediction_card(period, signal, number):
    if not os.path.exists("template.png"):
        print("[!] ERROR: template.png file kanom!")
        return None

    try:
        base_img = Image.open("template.png").convert("RGBA")
        width, height = base_img.size
        
        # 1024x1024 image-ku resize / scale panni handle panrom
        draw = ImageDraw.Draw(base_img)
        
        # Font setup (Image size-ku etha mathiri size)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        except Exception:
            font = ImageFont.load_default()

        # Signal color setup
        sig_upper = signal.upper()
        if "GREEN" in sig_upper or "SMALL" in sig_upper:
            sig_color = (0, 255, 128)      # Neon Green
        elif "RED" in sig_upper or "BIG" in sig_upper:
            sig_color = (255, 50, 70)       # Neon Red
        else:
            sig_color = (0, 220, 255)       # Cyan Blue

        # Text values
        period_text = f"#{period}"
        signal_text = sig_upper
        number_text = str(number) if number else "--"

        # --- EXACT BOX COORDINATES (1024x1024 Template) ---
        # 1. Period Box Center: (x=250, y=440)
        # 2. Signal Box Center: (x=500, y=440)
        # 3. Number Box Center: (x=750, y=440)

        # Helper function text-ah box center-la place panna
        def draw_centered_text(xy, text, fill_color, font_obj):
            bbox = font_obj.getbbox(text)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            draw.text((xy[0] - w / 2, xy[1] - h / 2), text, fill=fill_color, font=font_obj)

        # Boxes ulla crt-ah draw panrom
        draw_centered_text((250, 442), period_text, (255, 255, 255), font)
        draw_centered_text((500, 442), signal_text, sig_color, font)
        draw_centered_text((750, 442), number_text, (255, 215, 0), font)

        out_file = "send_prediction.jpg"
        base_img.convert("RGB").save(out_file, "JPEG", quality=95)
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

    print("\n--- [NEW SOURCE MSG RECEIVED] ---")
    print(raw_text)

    clean_text = unicodedata.normalize('NFKD', raw_text)

    # 1. Period Regex
    p_match = re.search(r'PERIOD.*?(\d+)', clean_text, re.IGNORECASE)
    period = p_match.group(1) if p_match else None

    # 2. Signal Regex
    s_match = re.search(r'(BIG|SMALL|GREEN|RED|VIOLET)', clean_text, re.IGNORECASE)
    signal = s_match.group(1).upper() if s_match else None

    # 3. Number Regex
    n_match = re.search(r'NUMBER.*?([0-9\/\s]+)', clean_text, re.IGNORECASE)
    number = n_match.group(1).strip() if n_match else ""

    if period and signal:
        print(f"[+] Parsed: Period={period} | Signal={signal} | Number={number}")
        
        # Keela caption-la neenga keta username mattum
        caption_text = "User name : @Gara00077"

        img_path = generate_prediction_card(period, signal, number)
        
        try:
            if img_path and os.path.exists(img_path):
                await client.send_file(TARGET_CHAT, img_path, caption=caption_text)
                print("[SUCCESS] Image with centered text sent to channel!")
            else:
                await client.send_message(TARGET_CHAT, caption_text)
        except Exception as send_err:
            print(f"[!] Send error: {send_err}")

print("[-] AKAZA AUTO Bot is Running...")
client.start()
client.run_until_disconnected()
