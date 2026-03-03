import os
import tempfile
import dropbox
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 🔐 Lendo tokens das variáveis de ambiente
TOKEN = os.environ["TOKEN"]
MEU_CHAT_ID = os.environ["MEU_CHAT_ID"]
DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]

# 📁 Pasta no Dropbox onde as fotos serão salvas
PASTA_DROPBOX = "/Fotos Residências"

def arquivo_existe_dropbox(dbx, nome):
    try:
        dbx.files_get_metadata(f"{PASTA_DROPBOX}/{nome}")
        return True
    except dropbox.exceptions.ApiError:
        return False

def upload_dropbox(dbx, caminho_local, nome_arquivo):
    with open(caminho_local, "rb") as f:
        dbx.files_upload(f.read(), f"{PASTA_DROPBOX}/{nome_arquivo}")

async def receber_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return

    legenda = update.message.caption

    if not legenda:
        await update.message.reply_text("❗ Envie a foto com o número do recibo na legenda.")
        return

    numero = legenda.strip()

    if not numero.isdigit():
        await update.message.reply_text("❗ A legenda deve conter apenas o número do recibo.")
        return

    nome_primeira = f"{numero}.jpg"
    nome_segunda = f"{numero}(1).jpg"

    dbx = dropbox.Dropbox(DROPBOX_TOKEN)

    if not arquivo_existe_dropbox(dbx, nome_primeira):
        nome_final = nome_primeira
        tentativa = "1ª tentativa"
    elif not arquivo_existe_dropbox(dbx, nome_segunda):
        nome_final = nome_segunda
        tentativa = "2ª tentativa"
    else:
        await update.message.reply_text(f"⚠ Recibo {numero} já possui 2 tentativas registradas.")
        return

    foto = update.message.photo[-1]
    file = await context.bot.get_file(foto.file_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        caminho_tmp = tmp.name

    await file.download_to_drive(caminho_tmp)
    upload_dropbox(dbx, caminho_tmp, nome_final)
    os.remove(caminho_tmp)

    remetente = update.message.from_user
    nome_remetente = remetente.full_name or remetente.username or "Desconhecido"

    print(f"📸 Foto salva: {nome_final} | Enviada por: {nome_remetente} | {tentativa}")

    await update.message.reply_text(f"✅ Recibo {numero} - {tentativa} registrada com sucesso!")

    await context.bot.send_message(
        chat_id=MEU_CHAT_ID,
        text=(
            f"📸 Nova foto salva!\n"
            f"👤 Enviada por: {nome_remetente}\n"
            f"🧾 Recibo: {numero}\n"
            f"📌 Tentativa: {tentativa}\n"
            f"📁 Arquivo: {nome_final}"
        )
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, receber_foto))
    print("🤖 Bot rodando...")
    print("-" * 40)
        async def notificar_inicio():
        await app.bot.send_message(
            chat_id=MEU_CHAT_ID,
            text="🟢 Bot iniciado e rodando!"
        )

    import asyncio
    asyncio.run(notificar_inicio())
    
    app.run_polling()