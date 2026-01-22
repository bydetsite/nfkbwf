import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Получаем токен из переменных окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def find_duplicates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    
    # Разбиваем текст на строки
    lines = text.split('\n')
    
    # Находим дубликаты
    seen = set()
    duplicates = set()
    
    for line in lines:
        line = line.strip()
        if line and line in seen:
            duplicates.add(line)
        seen.add(line)
    
    # Формируем ответ
    if duplicates:
        response = "Найдены повторяющиеся строки:\n" + "\n".join(f"• {d}" for d in duplicates)
    else:
        response = "Повторяющихся строк не найдено"
    
    await update.message.reply_text(response)

def main():
    """Запуск бота"""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, find_duplicates))
    app.run_polling()

if __name__ == '__main__':
    main()
