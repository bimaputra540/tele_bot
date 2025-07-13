from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import re
import os
import openpyxl
from openpyxl import Workbook

TOKEN = "7902562393:AAEyVh_TaJ37T2SFxXT6zDykMfF43Ln7mYA"
ADMIN_ID = 6526506965  # Ganti dengan ID Telegram kamu

user_data = {}
excel_file = "data_user.xlsx"

# Buat file Excel jika belum ada
def init_excel():
    if not os.path.exists(excel_file):
        wb = Workbook()
        ws = wb.active
        ws.append(["Username Telegram", "Nama Shopee", "Link Produk", "Varian", "Jumlah", "Cookie"])
        wb.save(excel_file)

# Tambah baris data ke file Excel
def simpan_ke_excel(username, shopee_name, link, variant, quantity, cookie):
    wb = openpyxl.load_workbook(excel_file)
    ws = wb.active
    ws.append([username, shopee_name, link, variant, quantity, cookie])
    wb.save(excel_file)

# Validasi cookie
def is_valid_cookie(cookie: str) -> bool:
    return "SPC_EC" in cookie and "SPC_U" in cookie

# Validasi link Shopee dari browser & aplikasi HP
def is_valid_shopee_link(link: str) -> bool:
    return any([
        re.match(r"^https:\/\/(www\.)?shopee\.co\.id\/.+", link),         # link dari browser
        re.match(r"^https:\/\/shp\.ee\/.+", link),                        # link pendek
        re.match(r"^https:\/\/shope\.ee\/.+", link),                      # link pendek
        re.match(r"^https:\/\/shp\.id\/.+", link),                        # link pendek
        re.match(r"^https:\/\/s\.shopee\.co\.id\/.+", link),              # link pendek
    ])


# Mulai percakapan
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "ask_shopee_name"}
    await update.message.reply_text("👋 Halo! Masukkan nama akun Shopee kamu:")

# Tangani input pengguna
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()
    username = update.effective_user.username or "Tanpa Username"

    if user_id not in user_data:
        await update.message.reply_text("Silakan mulai dengan /start.")
        return

    step = user_data[user_id].get("step")
    
    if step == "ask_shopee_name":
        user_data[user_id]["shopee_name"] = message
        user_data[user_id]["step"] = "ask_cookie"
        await update.message.reply_text("✅ Nama Shopee disimpan.\nSekarang masukkan cookie Shopee kamu:")

    elif step == "ask_cookie":
        if is_valid_cookie(message):
            user_data[user_id]["cookie"] = message
            user_data[user_id]["step"] = "ask_product_link"
            await update.message.reply_text("✅ Cookie valid.\nSekarang kirim link produk Shopee kamu:")
        else:
            await update.message.reply_text("❌ Cookie tidak valid. Harus mengandung 'SPC_EC' dan 'SPC_U'.")

    elif step == "ask_product_link":
        if is_valid_shopee_link(message):
            user_data[user_id]["product_link"] = message
            user_data[user_id]["step"] = "ask_variant"
            await update.message.reply_text("✅ Link produk valid.\nJika produk punya varian, tulis variannya.\nJika tidak, ketik: TIDAK ADA")
        else:
            await update.message.reply_text("❌ Link produk tidak valid. Kirim link dari Shopee (browser atau aplikasi).")

    elif step == "ask_variant":
        user_data[user_id]["variant"] = message
        user_data[user_id]["step"] = "ask_quantity"
        await update.message.reply_text("✅ Varian disimpan.\nSekarang masukkan jumlah barang:")

    elif step == "ask_quantity":
        if message.isdigit():
            user_data[user_id]["quantity"] = int(message)
            user_data[user_id]["step"] = "done"

            simpan_ke_excel(
                username=username,
                shopee_name=user_data[user_id]["shopee_name"],
                link=user_data[user_id]["product_link"],
                variant=user_data[user_id]["variant"],
                quantity=user_data[user_id]["quantity"],
                cookie=user_data[user_id]["cookie"]
            )

            await update.message.reply_text(
                "🎉 ✅ Semua data disimpan!\n\n"
                "🙏 Terima kasih! Semoga dapat ya 🎉\n"
                "💸 Kalau berhasil, langsung payment ke 👉 @xzyeig"
            )

            # Kirim notifikasi ke admin
            admin_msg = (
                f"📥 Data baru dari @{username}:\n\n"
                f"👤 Nama Shopee: {user_data[user_id]['shopee_name']}\n"
                f"🔗 Link Produk: {user_data[user_id]['product_link']}\n"
                f"🎨 Varian: {user_data[user_id]['variant']}\n"
                f"📦 Jumlah Barang: {user_data[user_id]['quantity']}\n"
                f"🍪 Cookie: {user_data[user_id]['cookie']}"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
        else:
            await update.message.reply_text("❌ Masukkan angka yang valid untuk jumlah barang!")

    else:
        await update.message.reply_text("✅ Data sudah lengkap. Gunakan /start untuk mulai ulang.")

# Perintah bantuan
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Gunakan /start untuk mulai isi data.")

# Jalankan bot
init_excel()
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

print("✅ Bot aktif. Tekan Ctrl+C untuk menghentikan.")
app.run_polling()
