import logging
from telegram import Update, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = "8709897192:AAewR7otKiHb3DAa1jRxesJpOxvoKGTCKc"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

GRUPO_STAFF = {}
ADVERTENCIAS = {}
REGLAS = {}
EXTRAS = {}
FILTROS_PRO = {}

async def setstaffgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["staff_chat_id"] = update.effective_chat.id
    await update.message.reply_text("✅ ¡Este grupo ha sido configurado como el Grupo del Staff!")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Responde al mensaje que deseas reportar con /report.")
        return
    staff_id = context.bot_data.get("staff_chat_id")
    if not staff_id:
        await update.message.reply_text("❌ No hay un Grupo de Staff vinculado.")
        return
    msg = update.message.reply_to_message
    await context.bot.send_message(
        chat_id=staff_id,
        text=f"🚨 **REPORTE**\n👤 De: {update.effective_user.first_name}\n💬 {msg.text}\n🔗 {msg.link}",
        parse_mode="Markdown"
    )
    await update.message.reply_text("📲 Reporte enviado al staff.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Responde al mensaje del usuario que deseas banear.")
        return
    try:
        await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=update.message.reply_to_message.from_user.id)
        await update.message.reply_text("⛔ Usuario baneado con éxito.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Uso: /unban [ID]")
        return
    await context.bot.unban_chat_member(chat_id=update.effective_chat.id, user_id=int(context.args[0]))
    await update.message.reply_text("✅ Usuario desbaneado.")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Responde al usuario a silenciar.")
        return
    await context.bot.restrict_chat_member(
        chat_id=update.effective_chat.id,
        user_id=update.message.reply_to_message.from_user.id,
        permissions=ChatPermissions(can_send_messages=False)
    )
    await update.message.reply_text("🔇 Usuario silenciado.")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Responde al usuario.")
        return
    await context.bot.restrict_chat_member(
        chat_id=update.effective_chat.id,
        user_id=update.message.reply_to_message.from_user.id,
        permissions=ChatPermissions(can_send_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
    )
    await update.message.reply_text("🔊 Usuario desmuteado.")

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Responde al usuario a advertir.")
        return
    chat_id = update.effective_chat.id
    user_id = update.message.reply_to_message.from_user.id
    if chat_id not in ADVERTENCIAS:
        ADVERTENCIAS[chat_id] = {}
    ADVERTENCIAS[chat_id][user_id] = ADVERTENCIAS[chat_id].get(user_id, 0) + 1
    total = ADVERTENCIAS[chat_id][user_id]
    if total >= 3:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        ADVERTENCIAS[chat_id][user_id] = 0
        await update.message.reply_text(f"⚠️ Acumuló 3 advertencias y fue baneado.")
    else:
        await update.message.reply_text(f"⚠️ Advertencia ({total}/3).")

async def del_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        await update.message.reply_to_message.delete()
        await update.message.delete()

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        await context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=update.message.reply_to_message.message_id)
        await update.message.reply_text("📌 Mensaje anclado.")

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)
    if not texto:
        await update.message.reply_text("⚠️ Uso: /setrules [Texto]")
        return
    REGLAS[update.effective_chat.id] = texto
    await update.message.reply_text("✅ Reglas guardadas.")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = REGLAS.get(update.effective_chat.id, "No hay reglas definidas.")
    await update.message.reply_text(f"📋 **REGLAS:**\n\n{texto}", parse_mode="Markdown")

async def extra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Uso: /extra palabra respuesta")
        return
    chat_id = update.effective_chat.id
    if chat_id not in EXTRAS:
        EXTRAS[chat_id] = {}
    EXTRAS[chat_id][context.args[0].lower()] = " ".join(context.args[1:])
    await update.message.reply_text("✅ Auto-respuesta creada.")

async def setantispam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ [PRO] Uso: /setantispam palabra1 palabra2")
        return
    FILTROS_PRO[update.effective_chat.id] = context.args
    await update.message.reply_text("💎 [PRO] Filtro anti-spam activado.")

async def gestor_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    texto = update.message.text.lower() if update.message.text else ""
    if chat_id in FILTROS_PRO:
        for p in FILTROS_PRO[chat_id]:
            if p in texto:
                await update.message.delete()
                return
    if chat_id in EXTRAS:
        for p, r in EXTRAS[chat_id].items():
            if p in texto:
                await update.message.reply_text(r)
                break

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("setstaffgroup", setstaffgroup))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("del", del_msg))
    app.add_handler(CommandHandler("pin", pin))
    app.add_handler(CommandHandler("setrules", setrules))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("extra", extra))
    app.add_handler(CommandHandler("setantispam", setantispam))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gestor_mensajes))
    print("Bot activo...")
    app.run_polling()

if __name__ == "__main__":
    main()
