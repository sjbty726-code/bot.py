
import os
import json
from pathlib import Path

import telebot

TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable.")

bot = telebot.TeleBot(TOKEN)
DATA_FILE = Path("announcements.json")


def load_ads():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_ads(ads):
    DATA_FILE.write_text(
        json.dumps(ads, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def is_admin(message):
    if ADMIN_ID == 0 or message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "عذراً، هذا الأمر مخصص للمشرف فقط.")
        return False
    return True


@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.reply_to(
        message,
        "أهلاً بك في WOODE HUB.\n\n"
        "أوامر المشرف:\n"
        "/add نص الإعلان\n"
        "/photo ثم أرسل صورة مع وصف يبدأ بـ /photo\n"
        "/show عرض الإعلانات\n"
        "/delete حذف آخر إعلان"
    )


@bot.message_handler(commands=["add"])
def add_ad(message):
    if not is_admin(message):
        return

    text = message.text.partition(" ")[2].strip()
    if not text:
        bot.reply_to(message, "اكتب الإعلان بعد الأمر، مثال:\n/add مرحباً بكم")
        return

    ads = load_ads()
    ads.append({"type": "text", "text": text})
    save_ads(ads)
    bot.reply_to(message, f"تم حفظ الإعلان رقم {len(ads)}.")


@bot.message_handler(commands=["photo"])
def photo_help(message):
    if not is_admin(message):
        return
    bot.reply_to(
        message,
        "لإضافة إعلان بصورة: أرسل الصورة مع وصفها في خانة التعليق، "
        "ثم اكتب /photo في بداية التعليق.\n"
        "مثال: /photo إعلان WOODE HUB"
    )


@bot.message_handler(content_types=["photo"])
def receive_photo(message):
    if not is_admin(message):
        return

    caption = (message.caption or "").strip()
    if not caption.startswith("/photo"):
        return

    description = caption[len("/photo"):].strip()
    ads = load_ads()
    ads.append({
        "type": "photo",
        "file_id": message.photo[-1].file_id,
        "caption": description,
    })
    save_ads(ads)
    bot.reply_to(message, f"تم حفظ الإعلان المصوّر رقم {len(ads)}.")


@bot.message_handler(commands=["show"])
def show_ads(message):
    if not is_admin(message):
        return

    ads = load_ads()
    if not ads:
        bot.reply_to(message, "لا توجد إعلانات محفوظة حالياً.")
        return

    bot.reply_to(message, f"عدد الإعلانات المحفوظة: {len(ads)}")
    for index, ad in enumerate(ads, start=1):
        if ad.get("type") == "photo":
            bot.send_photo(
                message.chat.id,
                ad["file_id"],
                caption=f"إعلان رقم {index}\n{ad.get('caption', '')}",
            )
        else:
            bot.send_message(
                message.chat.id,
                f"إعلان رقم {index}\n{ad.get('text', '')}",
            )


@bot.message_handler(commands=["delete"])
def delete_ad(message):
    if not is_admin(message):
        return

    ads = load_ads()
    if not ads:
        bot.reply_to(message, "لا توجد إعلانات لحذفها.")
        return

    ads.pop()
    save_ads(ads)
    bot.reply_to(message, "تم حذف آخر إعلان.")


if __name__ == "__main__":
    print("WOODE HUB bot is running...")
    bot.infinity_polling(skip_pending=True)
