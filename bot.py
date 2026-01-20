import asyncio
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = 'YOUR_BOT_TOKEN'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class ListComparison(StatesGroup):
    waiting_first_list = State()
    waiting_second_list = State()

# Клавиатура с кнопками
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("📊 Сравнить списки"))
keyboard.add(KeyboardButton("❓ Помощь"))

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply(
        "🤖 Бот для сравнения списков и поиска дубликатов!\n\n"
        "Я могу:\n"
        "• Найти дубликаты между двумя списками\n"
        "• Показать результаты в виде таблицы\n"
        "• Подсчитать статистику\n\n"
        "Нажми '📊 Сравнить списки' или отправь /compare",
        reply_markup=keyboard
    )

@dp.message_handler(lambda message: message.text == "📊 Сравнить списки")
@dp.message_handler(commands=['compare'])
async def start_comparison(message: types.Message):
    await message.reply(
        "📋 Отправь первый список\n"
        "💡 Элементы можно разделять запятыми или каждый с новой строки"
    )
    await ListComparison.waiting_first_list.set()

@dp.message_handler(state=ListComparison.waiting_first_list)
async def get_first_list(message: types.Message, state: FSMContext):
    first_list = [item.strip() for item in message.text.replace(',', '\n').split('\n') if item.strip()]
    
    if not first_list:
        await message.reply("❌ Список пустой! Отправь что-нибудь:")
        return
    
    await state.update_data(first_list=first_list, first_list_raw=message.text)
    await message.reply(f"✅ Получил {len(first_list)} элементов\n📋 Теперь отправь второй список:")
    await ListComparison.waiting_second_list.set()

@dp.message_handler(state=ListComparison.waiting_second_list)
async def get_second_list(message: types.Message, state: FSMContext):
    second_list = [item.strip() for item in message.text.replace(',', '\n').split('\n') if item.strip()]
    
    if not second_list:
        await message.reply("❌ Список пустой! Отправь что-нибудь:")
        return
    
    data = await state.get_data()
    first_list = data.get('first_list', [])
    
    # Находим различия и дубликаты
    duplicates = list(set(first_list) & set(second_list))
    unique_first = list(set(first_list) - set(second_list))
    unique_second = list(set(second_list) - set(first_list))
    
    # Создаем подробный отчет
    report = f"""
📊 **РЕЗУЛЬТАТЫ СРАВНЕНИЯ**

📈 **Статистика:**
• Первый список: {len(first_list)} элементов
• Второй список: {len(second_list)} элементов
• Дубликаты: {len(duplicates)}
• Уникальные в 1-м: {len(unique_first)}
• Уникальные во 2-м: {len(unique_second)}

🔍 **Дубликаты:**
"""
    
    if duplicates:
        report += '\n'.join(f"• `{dup}`" for dup in sorted(duplicates))
    else:
        report += "• Дубликаты не найдены"
    
    if unique_first:
        report += f"\n\n📝 **Только в первом списке:**\n"
        report += '\n'.join(f"• `{item}`" for item in sorted(unique_first)[:10])
        if len(unique_first) > 10:
            report += f"\n• ... и еще {len(unique_first) - 10}"
    
    if unique_second:
        report += f"\n\n📝 **Только во втором списке:**\n"
        report += '\n'.join(f"• `{item}`" for item in sorted(unique_second)[:10])
        if len(unique_second) > 10:
            report += f"\n• ... и еще {len(unique_second) - 10}"
    
    # Создаем Excel файл если списки большие
    if len(first_list) > 50 or len(second_list) > 50:
        df_comparison = pd.DataFrame({
            'Статус': ['Дубликат' if item in duplicates else 'Только в 1-м' for item in first_list] + 
                     ['Только во 2-м' for item in unique_second],
            'Элемент': duplicates + unique_first + unique_second
        })
        
        excel_file = f"comparison_{message.from_user.id}.xlsx"
        df_comparison.to_excel(excel_file, index=False)
        
        with open(excel_file, 'rb') as file:
            await bot.send_document(message.chat.id, file, caption="📊 Подробный отчет в Excel")
    
    await message.reply(report, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    await state.finish()

@dp.message_handler(lambda message: message.text == "❓ Помощь")
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = """
🤖 **Как пользоваться ботом:**

1. Нажмите "📊 Сравнить списки"
2. Отправьте первый список (можно через запятую или с новой строки)
3. Отправьте второй список
4. Получите результаты!

**Примеры ввода:**
• `яблоко, банан, апельсин`
• 
