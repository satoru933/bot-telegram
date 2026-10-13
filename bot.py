import os
import re
from threading import Thread
from flask import Flask
import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# 1. Servidor web diminuto para mantenerlo gratis en Render
app = Flask('')

@app.route('/')
def home():
    return "¡Bot de Moderación activo 24/7!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# 2. Tu Token integrado
TOKEN = "8709897192:AAewR7otKiHb3DAa1jRxesJpOxvoKGTCKc"

# Palabras prohibidas (puedes agregar más separadas por coma)
PALABRAS_PROHIBIDAS = ["spam", "casino", "cripto", "estafa"]

# --- FUNCIONES DE MODERACIÓN TIPO GROUP HELP ---

# Mensaje de Bienvenida
async def bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"¡Hola {member.mention_html()}! 👋 Bienvenido/a al grupo. Por favor lee las reglas.",
            parse_mode="HTML"
        )

# Moderación de Mensajes (Links y Malas Palabras)
async def moderar_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text or ""
    user = update.message.from_user
    chat_id = update.message.chat_id

    # Verificar si el usuario es administrador (los admins no sufren moderación)
    member = await context.bot.get_chat_member(chat_id, user.id)
    if member.status in ['administrator', 'creator']:
        return

    # 1. Eliminar Enlaces (Anti-link)
    if "http://" in texto or "https://" in texto or "t.me/" in texto:
        try:
            await update.message.delete()
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ {user.mention_html()}, no se permiten enlaces en este grupo.",
                parse_mode="HTML"
            )
            return
        except Exception as e:
            print(f"Error al borrar mensaje: {e}")

    # 2. Eliminar Palabras Prohibidas
    for palabra in PALABRAS_PROHIBIDAS:
        if re.search(rf"\b{palabra}\b", texto, re.IGNORECASE):
            try:
                await update.message.delete()
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ {user.mention_html()}, tu mensaje contenía contenido no permitido.",
                    parse_mode="HTML"
                )
                return
            except Exception as e:
                print(f"Error al borrar mensaje: {e}")

# Comando /ban
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Responde al mensaje del usuario que deseas banear.")
        return
    user_to_ban = update.message.reply_to_message.from_user
    await context.bot.ban_chat_member(update.message.chat_id, user_to_ban.id)
    await update.message.reply_text(f"🚫 {user_to_ban.mention_html()} ha sido baneado.", parse_mode="HTML")

# Comando /mute (Silenciar)
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Responde al mensaje del usuario que deseas silenciar.")
        return
    user_to_mute = update.message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=False)
    await context.bot.restrict_chat_member(update.message.chat_id, user_to_mute.id, permissions=permissions)
    await update.message.reply_text(f"🤐 {user_to_mute.mention_html()} ha sido silenciado.", parse_mode="HTML")

# Comando /unmute (Desmutear)
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Responde al mensaje del usuario que deseas desmutear.")
        return
    user_to_unmute = update.message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
    await context.bot.restrict_chat_member(update.message.chat_id, user_to_unmute.id, permissions=permissions)
    await update.message.reply_text(f"🔊 {user_to_unmute.mention_html()} ya puede hablar de nuevo.", parse_mode="HTML")

# --- INICIO DEL BOT ---
def main():
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, moderar_mensajes))

    application.run_polling()

if __name__ == '__main__':
    keep_alive()
    main()
