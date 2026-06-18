import os
import csv
import time
import json
import re
import telebot
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise SystemExit(
        "❌ Missing environment variables.\n"
        "   Run:\n"
        "   export TELEGRAM_TOKEN='your_bot_token'\n"
        "   export GROQ_API_KEY='your_groq_key'"
    )

CHAT_ID_FILE = "last_chat_id.txt"
if not os.path.exists(CHAT_ID_FILE):
    raise SystemExit(
        "❌ 'last_chat_id.txt' မတွေ့ပါ။\n"
        "   အရင်ဆုံး get_csv.py ကို runပြီး CSV ဖိုင်တင်ပေးပါ။"
    )

with open(CHAT_ID_FILE, 'r') as f:
    CHAT_ID = f.read().strip()

INPUT_FILE = "raww_addrA.csv"
ADDRESS_COLUMN = None
BATCH_SIZE = 20
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 1.5
BATCH_PAUSE = 3.0

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are an expert Myanmar Address Parser trained on MIMU standards.
Parse unstructured Myanmar address strings into structured JSON fields.

RULES:
1. home_no: house/building/block number. "N/A" if missing.
2. floor_room: floor/room/unit. "N/A" if missing.
3. street_landmark: street, lane, quarter, village, or landmark.
4. ward: specific Ward if mentioned. Otherwise "N/A".
5. village: only if "ကျေးရွာ" is explicit. Otherwise "N/A".
6. township: Township (မြို့နယ်).7. city: "Yangon", "Mandalay", "Nay Pyi Taw", etc.
8. division_state: MUST infer from township/city.
   - Yangon townships -> "Yangon Region"
   - Mandalay townships -> "Mandalay Region"
   - Nay Pyi Taw -> "Nay Pyi Taw Union Territory"
   - Bago/Pyay -> "Bago Region"
   - Mawlamyine -> "Mon State"
   - Sittwe/Maungdaw -> "Rakhine State"
9. original_address: exact input string.
10. status: "Success" or "Invalid_Address".

Return ONLY raw JSON (no markdown)."""

def clean_address(raw_text):
    text = raw_text.strip()
    if not text or text.lower() in ["blank", "null", "none", "-", "n/a"]:
        return ""
    text = re.sub(r'^No[-\.]?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Address[:\s]*', '', text, flags=re.IGNORECASE)
    return text

def read_addresses_from_csv(filepath):
    addresses = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        sample = f.read(4096)
        f.seek(0)
        has_header = False
        try:
            has_header = csv.Sniffer().has_header(sample)
        except csv.Error:
            has_header = False

        if has_header:
            reader = csv.DictReader(f)
            addr_col = ADDRESS_COLUMN
            if not addr_col:
                for col in reader.fieldnames or []:
                    if col and any(kw in col.lower() for kw in ['address', 'addr', 'လိပ်စာ', 'location']):
                        addr_col = col
                        break
                if not addr_col:
                    addr_col = reader.fieldnames[0]
            for row in reader:
                val = (row.get(addr_col) or '').strip()
                if val:
                    addresses.append(val)
        else:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():                    addresses.append(row[0].strip())
    return addresses

def parse_with_groq(address):
    for attempt in range(MAX_RETRIES):
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Parse this address: {address}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                timeout=10
            )
            content = completion.choices[0].message.content
            result = json.loads(content)
            result.setdefault("division_state", "N/A")
            result.setdefault("status", "Success")
            return result
        except json.JSONDecodeError:
            print(f"JSON Decode Error (attempt {attempt+1}): {content[:50]}...")
            time.sleep(2)
        except Exception as e:
            print(f"API Error (attempt {attempt+1}): {e}")
            time.sleep(2)
    return {
        "home_no": "N/A", "floor_room": "N/A", "street_landmark": "N/A",
        "ward": "N/A", "village": "N/A", "township": "N/A", "city": "N/A",
        "division_state": "N/A", "original_address": address,
        "status": "System_Error: Max retries exceeded"
    }

def main():
    if not os.path.exists(INPUT_FILE):
        msg = f"❌ '{INPUT_FILE}' not found. Run get_csv.py first."
        print(msg)
        bot.send_message(CHAT_ID, msg)
        return

    raw_addresses = read_addresses_from_csv(INPUT_FILE)
    total_count = len(raw_addresses)
    if total_count == 0:
        bot.send_message(CHAT_ID, "⚠️ CSV ဖိုင်ထဲမှာ လိပ်စာ မတွေ့ပါ။")
        return

    bot.send_message(
        CHAT_ID,
        f"🚀 စတင်ဆောင်ရွက်နေပါပြီ...\n"        f"စုစုပေါင်း လိပ်စာ {total_count} ခုကို စစ်ဆေးပါမည်။\n"
        f"(MIMU Standard & Groq AI Enabled)"
    )

    batch_results = []
    batch_number = 1
    start_time = time.time()

    for index, raw_addr in enumerate(raw_addresses, 1):
        clean_addr = clean_address(raw_addr)
        if not clean_addr:
            result = {
                "home_no": "N/A", "floor_room": "N/A", "street_landmark": "N/A",
                "ward": "N/A", "village": "N/A", "township": "N/A", "city": "N/A",
                "division_state": "N/A", "original_address": raw_addr,
                "status": "Skipped_Blank"
            }
        else:
            print(f"[{index}/{total_count}] {clean_addr[:40]}...")
            result = parse_with_groq(clean_addr)
            result["original_address"] = raw_addr

        batch_results.append(result)

        if len(batch_results) >= BATCH_SIZE or index == total_count:
            batch_file_name = f"batch_{batch_number}_results.json"
            with open(batch_file_name, 'w', encoding='utf-8') as f:
                json.dump(batch_results, f, ensure_ascii=False, indent=2)

            success_count = sum(1 for r in batch_results if r.get('status') == 'Success')
            msg = (
                f"📦 *Batch {batch_number} ပြီးစီး*\n"
                f"✅ အောင်မြင်မှု: {success_count}/{len(batch_results)}\n"
                f"📂 ဖိုင်: `{batch_file_name}`\n"
                f"⏳ ကုန်ဆုံးချိန်: {time.time() - start_time:.1f}s"
            )
            try:
                bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                with open(batch_file_name, 'rb') as doc:
                    bot.send_document(CHAT_ID, doc, caption=f"Batch {batch_number}")
                os.remove(batch_file_name)
            except Exception as e:
                print(f"Telegram Send Error: {e}")

            batch_results = []
            batch_number += 1
            if index != total_count:
                time.sleep(BATCH_PAUSE)
        time.sleep(RATE_LIMIT_DELAY)
    total_time = time.time() - start_time
    bot.send_message(
        CHAT_ID,
        f"🎉 *အလုပ်ပြီးစီး!*\n"
        f"စုစုပေါင်း: {total_count}\n"
        f"ကြာချိန်: {total_time/60:.2f} မိနစ်\n"
        f"စနစ်: Groq Cloud + MIMU Logic",
        parse_mode="Markdown"
    )
    print(f"Completed in {total_time/60:.2f} minutes.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        bot.send_message(CHAT_ID, "⛔ လုပ်ငန်းစဉ်ကို အသုံးပြုသူမှ ရပ်တန့်လိုက်သည်။")
    except Exception as e:
        try:
            bot.send_message(CHAT_ID, f"💥 Critical Error: {e}")
        except Exception:
            pass
        print(f"Critical Error: {e}")
