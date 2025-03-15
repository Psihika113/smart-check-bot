import logging
import os
import pytesseract
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from fpdf import FPDF

# Настройки бота
TOKEN = os.getenv("TOKEN")  # Переменная окружения для безопасности

db = sqlite3.connect("receipts.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS receipts (id INTEGER PRIMARY KEY, data TEXT)")
db.commit()

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Клавиатура команд
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("📄 Добавить чек"))
keyboard.add(KeyboardButton("📊 Скачать PDF"))

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.answer("Привет! Я помогу тебе с чеками. Выбери команду:", reply_markup=keyboard)

@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.DOCUMENT])
async def handle_receipt(message: types.Message):
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    downloaded_file = await bot.download_file(file_path)
    
    file_name = f"receipt_{message.from_user.id}.jpg"
    with open(file_name, "wb") as new_file:
        new_file.write(downloaded_file.read())
    
    text = pytesseract.image_to_string(file_name, lang="rus")
    cursor.execute("INSERT INTO receipts (data) VALUES (?)", (text,))
    db.commit()
    os.remove(file_name)
    await message.answer("✅ Чек обработан и добавлен в базу!")

@dp.message_handler(lambda message: message.text == "📊 Скачать PDF")
async def generate_pdf(message: types.Message):
    cursor.execute("SELECT * FROM receipts")
    rows = cursor.fetchall()
    
    if not rows:
        await message.answer("Нет данных для создания PDF.")
        return
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, "Отсканированные чеки", ln=True, align='C')
    pdf.ln(10)
    
    for row in rows:
        pdf.multi_cell(0, 10, f"Чек {row[0]}:\n{row[1]}\n", border=0)
        pdf.ln(5)
    
    pdf_file = f"receipts_{message.from_user.id}.pdf"
    pdf.output(pdf_file)
    
    with open(pdf_file, "rb") as doc:
        await message.answer_document(types.InputFile(doc, filename=pdf_file))
    
    os.remove(pdf_file)

async def main():
    dp.include_router(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

    os.remove(pdf_file)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
