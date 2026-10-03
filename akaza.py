import os
import re
import unicodedata
from telethon import TelegramClient, events
from PIL import Image, ImageDraw, ImageFont

# ================= TELEGRAM CONFIG =================
API_ID = 37846916
API_HASH = "4e3784d4d626f589b50158e92cc93d5d"

SESSION_NAME = "akaza_user"

# Usernames crt-ah @ oda configure panniyachu
SOURCE_CHAT = "@predictor7700"          
TARGET_CHAT = "@akazagodmodeelite"      

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ================= IMAGE GENERATOR =================
def generate_prediction_card(period, signal, number):
    # Template image illana None return pannum (crash aagathu)
    if not os.path.exists("template.png"):
        print("[!] ERROR: template.png file kanom! GitHub repo-la template.png upload pannunga.")
        return None

    try:
        base_img = Image.open("template.png").convert("RGBA")
        width, height = base_img.size
        
        overlay = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        try:
            font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
            font_small = ImageFont.truetype("DejaVuSans.ttf", 34)
        except Exception:
            font_large = font_small = ImageFont.load_default()

        sig_upper = signal.upper()
        if "GREEN" in sig_upper or "SMALL" in sig_upper:
            sig_color = (0, 255, 128)      # Neon Green
        elif "RED" in sig_upper or "BIG" in sig_upper:
            sig_color = (255, 50, 70)       # Neon Red
        else:
            sig_color = (0, 220, 255)       # Cyan Blue

        # Neon bar box
        strip_y = height - 220
        draw.rectangle([(80, strip_y), (width - 80, height - 60)], fill=(10, 15, 30, 220), outline=(0, 200, 255, 255), width=3)
        
        draw.text((120, strip_y + 25), f"PERIOD : #{period}", fill=(255, 255, 255), font=font_small)
        draw.text((120, strip_y + 85), f"SIGNAL : {sig_upper}", fill=sig_color, font=font_large)
        if number:
            draw.text((width - 340, strip_y + 85), f"NUM: {number}", fill=(255, 215, 0), font=font_large)

        final_img = Image.alpha_composite(base_img, overlay).convert("RGB")
        out_file = "send_prediction.jpg"
        final_img.save(out_file, "JPEG", quality=95)
        return out_file
    except Exception as img_err:
        print(f"[!] Image create panrathula error: {img_err}")
        return None

# ================= MESSAGE LISTENER =================
@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def message_handler(event):
    raw_text = event.raw_text
    if not raw_text:
        return

    print("\n--- [NEW SOURCE MSG RECEIVED] ---")
    print(raw_text)
    print("---------------------------------")

    # Math unicode fonts normal text-ah mathum
    clean_text = unicodedata.normalize('NFKD', raw_text)

    # 1. Period Regex
    p_match = re.search(r'PERIOD.*?(\d+)', clean_text, re.IGNORECASE)
    period = p_match.group(1) if p_match else None

    # 2. Signal Regex (BIG / SMALL / GREEN / RED / VIOLET)
    s_match = re.search(r'(BIG|SMALL|GREEN|RED|VIOLET)', clean_text, re.IGNORECASE)
    signal = s_match.group(1).upper() if s_match else None

    # 3. Number Regex
    n_match = re.search(r'NUMBER.*?([0-9\/\s]+)', clean_text, re.IGNORECASE)
    number = n_match.group(1).strip() if n_match else ""

    if period and signal:
        print(f"[+] Prediction Parsed: Period={period} | Signal={signal} | Number={number}")
        
        caption_text = (
            f"⚡ **AKAZA AUTO PREDICTION** ⚡\n\n"
            f"🎯 **Period:** `#{period}`\n"
            f"🔮 **Prediction:** **{signal}**\n"
            f"🔢 **Number:** `{number}`\n\n"
            f"🚀 *Fast & Automated Signals*"
        )

        img_path = generate_prediction_card(period, signal, number)
        
        try:
            if img_path and os.path.exists(img_path):
                await client.send_file(TARGET_CHAT, img_path, caption=caption_text)
                print("[SUCCESS] Image sent to Target Channel!")
            else:
                # Oruvelai template.png illana crash aagama Text-avathu pogum
                await client.send_message(TARGET_CHAT, caption_text)
                print("[SUCCESS] Text message sent to Target Channel (Template image missing)!")
        except Exception as send_err:
            print(f"[!] Send panrathula error: {send_err}")
    else:
        print("[-] Message vandhuchu aana Signal/Period extract aagala (Regex mismatch).")

async def main():
    print("[-] Checking target channel connection...")
    try:
        target_entity = await client.get_entity(TARGET_CHAT)
        print(f"[+] Connected to Target Channel: {target_entity.title}")
    except Exception as e:
        print(f"[!] Target channel connect panna mudila: {e}")
        print("NOTE: Unga akaza_user account intha channel-la Admin-ah irukannu check pannunga!")

    print("[-] AKAZA AUTO Bot is Running and Waiting for Signals...")

client.start()
client.loop.run_until_complete(main())
client.run_until_disconnected()
