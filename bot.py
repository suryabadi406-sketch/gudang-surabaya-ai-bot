import os
import logging
from openai import AsyncOpenAI
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Kamu adalah admin customer service toko Gudang Borongan Surabaya.

ATURAN:
- Jawab menggunakan Bahasa Indonesia.
- Jawaban harus singkat, jelas, ramah, dan natural seperti admin manusia.
- Maksimal 1-2 kalimat.
- Jangan menjawab panjang lebar.
- Toko berlokasi di Surabaya.
- Fokus menjawab pertanyaan calon pembeli mengenai toko, produk, pemesanan, dan pengiriman.
- Jangan mengarang harga, stok, alamat lengkap, nomor rekening, atau informasi yang belum diketahui.
- Jika informasi tidak diketahui, arahkan secara singkat untuk menunggu admin.
- Jika ditanya apakah toko amanah/terpercaya, jawab secara positif dan singkat tanpa mengarang bukti, testimoni, atau jaminan.
- Jangan menawarkan mengirim bukti apa pun.
"""

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        return False

    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )

    return member.status in ("administrator", "creator")


async def reply_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if update.effective_user.is_bot:
        return

    # Di grup: jangan balas admin/owner
    if update.effective_chat.type != ChatType.PRIVATE:
        try:
            if await is_admin(update, context):
                return
        except Exception as e:
            logging.error("Gagal cek admin: %s", e)
            return

    try:
        response = await client.responses.create(
            model="gpt-5-mini",
            instructions=SYSTEM_PROMPT,
            input=update.message.text,
            max_output_tokens=100,
        )

        answer = response.output_text.strip()

        if answer:
            await update.message.reply_text(answer)

    except Exception as e:
        logging.error("AI error: %s", e)
        await update.message.reply_text(
            "Mohon tunggu sebentar kak, admin akan membantu."
        )


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, reply_ai)
    )

    print("Bot aktif...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
