import os
import tempfile
import dropbox
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 🔐 Token do seu bot
TOKEN = "8554074734:AAEAs_VH3xpkNTf7cY7vsnuG0iUtX6X9Sw8"

# 💬 Seu chat_id pessoal
MEU_CHAT_ID = "8276238327"

# 📦 Token do Dropbox
DROPBOX_TOKEN = "sl.u.AGUN0mcWlDrP2aMJ4ooqKGPQFriDqximfV_JS7zBe6d3DEIWQb7EugvvzAG2c9J8EgPA0bkV0pRqK1dzBL7T_w1waQqiT59Z9MLPaZLNsgnBtXy-CNC6IQzFdiu3Au0vy7EWzTLki6q7aOvbYLjaT_5JaI3z3P0vXSyyy3UgmE4MYvZ1L8nc4KwYw_Ysr1I1UXTJo2h_EpTE2cKZ145j-3kumjSADZ-KuIMtNl7wR87MXuefV-6DTaipO0RpPUGPMBVizPyb9aPNzp8VM9exfMlGXSGnStltO-uK_z4vZcrwTuQL8IjnAIs9bdsF-WR3Xdg__TOLzsL-tsQEcuCQwPIgcPzC9k4JH0zSn6ouUUM7Go72PejGxv5AG-I03wGvcv-hA6DqmW8qqKputCjDCxOO1ZB80p9KdAmn5GMY0FcQCSnI3fZKl0BRuNN9RUVTzzclPPw9m7atO1WAas0U0Ruh0fgbGBOO_XW3LcIRfiYuN-_ZXkK1Tz4okhXuciumeXRnaQ6g780N5E6i3UXSoxLlam8Nop6BI_-QmH2R6k2NXio--1hOUAdncwOcwSFDjg1ag_PVOPAjBmPAWh5lQaiBu2TlpJgnZ8iAMKIc3K_4vlmBZtqHvnTvLzGEqYPIefrJXzzPLwBxlV-OCuJ5vsQ-DhTcctEugJkfqbZ8_sWIJgPGgCvxs5ulHDdNTUhdqQFAUds74BrG4iq94V9cgB40rF76NJqkBSGU3mjnV9H3W-S3J1YH-d-LP9tmtpEOB81CI_5fLuQyOS0mSMTd2dIKYUtuDiJ8miBm08ANqPD3dFFpqXqLQ8Js1qonAmfpqegVKW-Z2tT4RjnqwWvAkKn-c960dAT6b-uhDPwPIh1wr5dl9RpRR5-3meXDJukeULLMeS3vyIHco7TZuluMrWCkDlYl7MM0pH5SI5ZEE-K2cf1SSgBxe910lnHFr-JQ-TUlerQqLlmzR26LUeB5ceLg3EHt0rB2oU6tjU2OubEOB28ij4A9ma-oHT0LMDqaa0Wjb0bh5jN2SMFUYYWIbg2iYpgC4aAWLdaMWjl57giQqCDLbmXE9pPBxzedPAAulDTphjTPRq7-OljPaMycOQboxsPyM8acfPLoIGUyKO7ZZjRFIU1nimauZn_2ViOY_05JbfH2sR6aOvgUcD1jzwTci3qSvggdmRTdzA5bhwmkTMlPqMSHMDr2EEpJ4nEnS00aCF1Fd9ANVlbXHD3qPUYkUkv6-nAvXgc3RSk6MeiH3TpigLbK0Jx_uy-z9ldJp0s4kodKakznzlG2WficgpDiWqPvJfKKwmS51lJrPZpduQ"

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

    # 📥 Baixar foto temporariamente e fazer upload pro Dropbox
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
    print(f"📁 Pasta Dropbox: {PASTA_DROPBOX}")
    print(f"👤 Notificações para o chat_id: {MEU_CHAT_ID}")
    print("-" * 40)
    app.run_polling()