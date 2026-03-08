"""
Telegram Bot - Claude AI Destekli Sohbet Botu
Kurulum:
    pip install python-telegram-bot anthropic

Kullanım:
    1. .env dosyasına TELEGRAM_TOKEN ve ANTHROPIC_API_KEY ekle
    2. python telegram_bot.py
"""

import logging
import os
from anthropic import Anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- Loglama ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Anthropic istemcisi ---
anthropic = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY"))

# Kullanıcı başına konuşma geçmişi (bellek)
conversation_histories: dict[int, list[dict]] = {}

SYSTEM_PROMPT = """Sen yardımsever, zeki ve samimi bir Türkçe asistansın. 
Kullanıcılarla doğal, akıcı bir şekilde Türkçe konuş. 
Sorulara net ve anlaşılır yanıtlar ver. Gerektiğinde emoji kullanabilirsin."""


# --- Komut Handler'ları ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot başlatıldığında karşılama mesajı."""
    user = update.effective_user
    conversation_histories[user.id] = []  # Geçmişi sıfırla
    await update.message.reply_text(
        f"Merhaba {user.first_name}! 👋\n\n"
        "Ben Claude AI tarafından desteklenen bir sohbet botuyum.\n"
        "Sana her konuda yardımcı olabilirim!\n\n"
        "📌 Komutlar:\n"
        "/start - Sohbeti yeniden başlat\n"
        "/help - Yardım menüsü\n"
        "/clear - Konuşma geçmişini temizle\n\n"
        "Haydi, sohbet edelim! 🚀"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yardım mesajı."""
    await update.message.reply_text(
        "🤖 *Claude AI Sohbet Botu*\n\n"
        "Bu bot, Anthropic'in Claude yapay zekası ile çalışır.\n\n"
        "*Nasıl Kullanılır?*\n"
        "• Bana herhangi bir şey yaz, sana yanıt vereyim!\n"
        "• Konuşma geçmişini hatırlıyorum, bağlamı koruyorum.\n\n"
        "*Komutlar:*\n"
        "/start - Sohbeti yeniden başlat\n"
        "/help - Bu mesajı göster\n"
        "/clear - Konuşma geçmişini temizle\n\n"
        "💡 İpucu: Uzun sorular, kodlama, çeviri, analiz gibi her konuda yardımcı olabilirim!",
        parse_mode="Markdown"
    )


async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Konuşma geçmişini temizle."""
    user = update.effective_user
    conversation_histories[user.id] = []
    await update.message.reply_text(
        "🗑️ Konuşma geçmişin temizlendi!\n"
        "Yeni bir sohbete başlayabiliriz."
    )


# --- Mesaj Handler ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı mesajını Claude API'ye ilet ve yanıtı gönder."""
    user = update.effective_user
    user_message = update.message.text

    # Yazıyor... göstergesi
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Geçmiş yoksa oluştur
    if user.id not in conversation_histories:
        conversation_histories[user.id] = []

    # Kullanıcı mesajını geçmişe ekle
    conversation_histories[user.id].append({
        "role": "user",
        "content": user_message
    })

    # Geçmişi max 20 mesajla sınırla (token tasarrufu)
    if len(conversation_histories[user.id]) > 20:
        conversation_histories[user.id] = conversation_histories[user.id][-20:]

    try:
        # Claude API çağrısı
        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation_histories[user.id]
        )

        assistant_reply = response.content[0].text

        # Yanıtı geçmişe ekle
        conversation_histories[user.id].append({
            "role": "assistant",
            "content": assistant_reply
        })

        await update.message.reply_text(assistant_reply)

    except Exception as e:
        logger.error(f"Claude API hatası: {e}")
        await update.message.reply_text(
            "⚠️ Bir hata oluştu, lütfen tekrar dene.\n"
            f"Hata: {str(e)}"
        )


# --- Ana Fonksiyon ---

def main() -> None:
    """Botu başlat."""
    telegram_token = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")

    if telegram_token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("❌ HATA: TELEGRAM_TOKEN ayarlanmamış!")
        print("Lütfen aşağıdaki gibi çalıştır:")
        print("  export TELEGRAM_TOKEN='your_token_here'")
        print("  export ANTHROPIC_API_KEY='your_api_key_here'")
        print("  python telegram_bot.py")
        return

    app = Application.builder().token(telegram_token).build()

    # Handler'ları kaydet
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot başlatıldı! Durdurmak için Ctrl+C")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
