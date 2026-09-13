import os
import logging
import threading

from flask import Flask
from openai import AsyncOpenAI
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# KONFIGURASI
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = AsyncOpenAI(api_key=OPENAI_API_KEY)


# =========================
# SERVER UNTUK RENDER
# =========================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Gudang Surabaya AI Bot aktif", 200


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =========================
# AI BOT TELEGRAM
# =========================

SYSTEM_PROMPT = """
Kamu adalah admin customer service Gudang Borongan Surabaya.

Tugas kamu membantu menjawab pertanyaan calon pembeli dengan bahasa Indonesia
yang singkat, sopan, natural, dan tidak terlihat seperti robot.

Toko menjual barang perabot, barang cuci gudang, barang retur,
dan barang borongan.

Jangan mengarang harga, stok, alamat, nomor rekening, ongkir,
atau informasi produk yang belum diberikan.

Jika informasi tidak diketahui, arahkan pelanggan untuk menunggu admin.
"""


async def jawab_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message or not message.text:
        return

    # Hanya merespons grup/supergroup
    if update.effective_chat.type not in (
        ChatType.GROUP,
        ChatType.SUPERGROUP,
    ):
        return

    # Jangan membalas pesan dari bot
    if update.effective_user and update.effective_user.is_bot:
        return

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": message.text,
                },
            ],
            max_tokens=250,
            temperature=0.7,
        )

        jawaban = response.choices[0].message.content

        if jawaban:
            await message.reply_text(jawaban)

    except Exception as error:
        logging.exception("Terjadi error: %s", error)


# =========================
# JALANKAN BOT
# =========================

def main():
    # Jalankan server Render
    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    # Jalankan Telegram bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            jawab_ai,
        )
    )

    print("Gudang Surabaya AI Bot aktif...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
