import os
import tempfile
import json
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 🔐 Tokens das variáveis de ambiente
TOKEN = os.environ["TOKEN"]
MEU_CHAT_ID = os.environ["MEU_CHAT_ID"]
DROPBOX_APP_KEY = os.environ["DROPBOX_APP_KEY"]
DROPBOX_APP_SECRET = os.environ["DROPBOX_APP_SECRET"]
DROPBOX_REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]

# 📁 Caminhos no Dropbox
PASTA_DROPBOX = "/Fotos Residências"
JSON_DROPBOX = "/Fotos Residências/Json/recibos_export.json"

def get_dropbox():
    """Cria conexão com Dropbox usando Refresh Token (nunca expira)"""
    return dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

def carregar_recibos(dbx):
    """Baixa e lê o JSON de recibos do Dropbox"""
    try:
        _, res = dbx.files_download(JSON_DROPBOX)
        dados = json.loads(res.content)
        return {str(item["codigo"]): int(item["tentativas"]) for item in dados}
    except Exception as e:
        print(f"Erro ao carregar recibos: {e}")
        return None


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

    dbx = get_dropbox()

    # ✅ Consulta o JSON gerado pelo Access
    recibos = carregar_recibos(dbx)

    if recibos is None:
        await update.message.reply_text("⚠️ Não foi possível consultar o banco de dados. Tente novamente.")
        return

    if numero not in recibos:
        await update.message.reply_text(f"❌ Recibo {numero} não encontrado na lista do dia.")
        return

    tentativas_anteriores = recibos[numero]

    if tentativas_anteriores >= 2:
        await update.message.reply_text(
            f"⛔ Recibo {numero} já possui {tentativas_anteriores} tentativas registradas. Limite atingido."
        )
        return

    # 📁 Define nome do arquivo baseado nas tentativas do JSON
    if tentativas_anteriores == 0:
        nome_final = f"{numero}.jpg"
        tentativa_atual = "1ª tentativa"
    elif tentativas_anteriores == 1:
        nome_final = f"{numero}(1).jpg"
        tentativa_atual = "2ª tentativa"
    else:
        await update.message.reply_text(f"⚠️ Recibo {numero} já possui 2 tentativas registradas.")
        return

    # 📥 Baixa e envia foto pro Dropbox
    foto = update.message.photo[-1]
    file = await context.bot.get_file(foto.file_id)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        caminho_tmp = tmp.name
    await file.download_to_drive(caminho_tmp)
    upload_dropbox(dbx, caminho_tmp, nome_final)
    os.remove(caminho_tmp)

    remetente = update.message.from_user
    nome_remetente = remetente.full_name or remetente.username or "Desconhecido"

    print(f"📸 Foto salva: {nome_final} | Enviada por: {nome_remetente} | {tentativa_atual}")

    await update.message.reply_text(
        f"✅ Recibo {numero} - {tentativa_atual} registrada com sucesso!\n"
        f"📋 Tentativas anteriores: {tentativas_anteriores}"
    )

    await context.bot.send_message(
        chat_id=MEU_CHAT_ID,
        text=(
            f"📸 Nova foto salva!\n"
            f"👤 Enviada por: {nome_remetente}\n"
            f"🧾 Recibo: {numero}\n"
            f"📌 {tentativa_atual}\n"
            f"📁 Arquivo: {nome_final}"
        )
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, receber_foto))

    async def pos_inicio(app):
        await app.bot.send_message(
            chat_id=MEU_CHAT_ID,
            text="🟢 Bot iniciado e rodando!"
        )

    app.post_init = pos_inicio
    print("🤖 Bot rodando...")
    print("-" * 40)
    app.run_polling()