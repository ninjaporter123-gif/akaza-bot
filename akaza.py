import re
import unicodedata
from telethon import TelegramClient, events

API_ID = 37846916
API_HASH = "4e3784d4d626f589b50158e92cc93d5d"

SOURCE = "@predictor7700"
DESTINATION = "@akazagodmodeelite"

client = TelegramClient("akaza_user", API_ID, API_HASH)

def clean_text(text):
    return unicodedata.normalize('NFKD', text)

@client.on(events.NewMessage(chats=SOURCE))
async def handler(event):
    raw_text = event.raw_text or ""
    text = clean_text(raw_text)

    print("\n--- NEW SOURCE MESSAGE ---")
    print(raw_text)

    # 1. WIN / LOSS RESULTS
    if "WIN" in text.upper() or "LOSS" in text.upper() or "RESULT" in text.upper():
        if "WIN" in text.upper():
            result_msg = "**ஜாலி பண்ணுங்க ❤️‍🔥🔥**"
        else:
            result_msg = "**சாரி  மச்சான் 🥺💔**"

        await client.send_message(DESTINATION, result_msg)
        print(f"✅ RESULT SENT: {result_msg}")
        return

    # 2. PREDICTION SIGNALS
    period = re.search(r"PERIOD[^\d]*(\d+)", text, re.IGNORECASE)
    signal = re.search(r"\b(BIG|SMALL|RED|GREEN)\b", text, re.IGNORECASE)
    number = re.search(r"NUMBER[^\d]*([\d/]+)", text, re.IGNORECASE)

    if not period or not signal or not number:
        print("❌ PERIOD / SIGNAL / NUMBER not found (Ignored)")
        return

    period_value = period.group(1)
    signal_value = signal.group(1).strip().upper()
    number_value = number.group(1).strip()

    message = f"""
╔══════════════════════════╗
       👑 𝐀𝐊𝐀𝐙𝐀 𝐆𝐎𝐃 👑
          𝐄𝐋𝐈𝐓𝐄
╚══════════════════════════╝

⏳ 𝐏𝐄𝐑𝐈𝐎𝐃
➜  **{period_value}**

🎯 𝐒𝐈𝐆𝐍𝐀𝐋
➜  **{signal_value}**

🔢 𝐍𝐔𝐌𝐁𝐄𝐑
➜  **{number_value}**

━━━━━━━━━━━━━━━━━━━━━━━━━━
        ⚡ 𝐆𝐎𝐃 𝐄𝐋𝐈𝐓𝐄 ⚡
     💎 𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐒𝐈𝐆𝐍𝐀𝐋 💎
━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ @Gara00077
"""
    await client.send_message(DESTINATION, message)
    print("✅ PREDICTION MESSAGE SENT TO DESTINATION")

print("🔥 AKAZA GOD ELITE STARTING...")
print("📡 Source:", SOURCE)
print("📤 Destination:", DESTINATION)

client.start()
print("✅ LOGIN SUCCESS")
print("👀 Waiting for new messages...")
client.run_until_disconnected()
