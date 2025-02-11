import logging
import os
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import asyncio

# .env faylidan BOT_TOKEN va CHANNEL_ID ni yuklash
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  # Bot tokeni
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Kanal IDsi

# Bot va dispetcherni ishga tushirish
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# E'lon berish holatlari
class YukHolati(StatesGroup):
    qayerdan = State()  # Yuk qayerdan yuboriladi
    qayerga = State()   # Yuk qayerga yuboriladi
    transport = State()  # Transport turi
    yuk_turi = State()  # Yuk turi
    narx = State()      # Narxi
    telefon = State()   # Telefon raqami
    telefon_confirm = State()  # Telefon raqamini tasdiqlash

# Start buyrug'i
@dp.message(F.text == "/start")
async def start(message: types.Message):
    tugmalar = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📝 E'lon berish")]], resize_keyboard=True)
    await message.answer(
        "Assalomu alaykum! Yuk tashish xizmatiga xush kelibsiz! 🚛\n"
        "E'lon berish uchun quyidagi tugmani bosing:",
        reply_markup=tugmalar
    )

@dp.message(F.text == "📝 E'lon berish")
async def yangi_elon(message: types.Message, state: FSMContext):
    await message.answer("🚚 Yuk qayerdan yuboriladi? (Shahar/tuman nomini yozing)")
    await state.set_state(YukHolati.qayerdan)

@dp.message(YukHolati.qayerdan)
async def qayerdan_olish(message: types.Message, state: FSMContext):
    await state.update_data(qayerdan=message.text)
    await message.answer("📍 Yuk qayerga yuboriladi? (Shahar/tuman nomini yozing)")
    await state.set_state(YukHolati.qayerga)

@dp.message(YukHolati.qayerga)
async def qayerga_yuborish(message: types.Message, state: FSMContext):
    await state.update_data(qayerga=message.text)
    await message.answer("🚛 Qanday transport vositasi kerak?\nMisol: Kamaz, Gazel, Porter")
    await state.set_state(YukHolati.transport)

@dp.message(YukHolati.transport)
async def transport_turi(message: types.Message, state: FSMContext):
    await state.update_data(transport=message.text)
    await message.answer("📦 Yukning turi qanday?\nMisol: Mebel, Qurilish mollari, Oziq-ovqat")
    await state.set_state(YukHolati.yuk_turi)

@dp.message(YukHolati.yuk_turi)
async def yuk_turi(message: types.Message, state: FSMContext):
    await state.update_data(yuk_turi=message.text)
    await message.answer("💰 Narxi qancha? (so'mda yozing)")
    await state.set_state(YukHolati.narx)

@dp.message(YukHolati.narx)
async def narx_qabul(message: types.Message, state: FSMContext):
    await state.update_data(narx=message.text)
    
    # Telefon raqami uchun tugma
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )
    
    await message.answer(
        "📱 Telefon raqamingizni yuboring yoki kiriting\n"
        "Misol: +998901234567 yoki 901234567",
        reply_markup=keyboard
    )
    await state.set_state(YukHolati.telefon)

@dp.message(YukHolati.telefon)
async def telefon_qabul(message: types.Message, state: FSMContext):
    # Kontakt orqali yuborilgan raqamni olish
    if message.contact:
        phone = message.contact.phone_number
    else:
        # Matnli xabar orqali yuborilgan raqamni tozalash
        phone = ''.join(filter(str.isdigit, message.text))
        
        # Raqam formati to'g'rilash
        if len(phone) == 9:  # 901234567 formatida
            phone = f"+998{phone}"
        elif len(phone) == 12 and phone.startswith("998"):  # 998901234567 formatida
            phone = f"+{phone}"
        elif not (len(phone) == 13 and phone.startswith("+")):  # Noto'g'ri format
            await message.answer(
                "❌ Noto'g'ri telefon raqam formati. Iltimos, quyidagi formatlardan birida kiriting:\n"
                "1. +998901234567\n"
                "2. 998901234567\n"
                "3. 901234567"
            )
            return
    
    # Telefon raqamni tasdiqlash
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data="confirm_phone"),
            InlineKeyboardButton(text="🔄 Qayta kiritish", callback_data="change_phone")
        ]
    ])
    
    await state.update_data(telefon=phone)
    await message.answer(
        f"Telefon raqamingiz: {phone}\nTo'g'rimi?",
        reply_markup=keyboard
    )
    await state.set_state(YukHolati.telefon_confirm)














@dp.callback_query(F.data == "change_phone")
async def change_phone(callback: types.CallbackQuery, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )
    await callback.message.answer(
        "📱 Yangi telefon raqamingizni yuboring yoki kiriting\n"
        "Misol: +998901234567 yoki 901234567",
        reply_markup=keyboard
    )
    await state.set_state(YukHolati.telefon)
    await callback.answer()






@dp.callback_query(F.data == "confirm_phone")
async def confirm_phone(callback: types.CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        
        username = f"\n👤 @{callback.from_user.username}" if callback.from_user.username else ""
        
        elon_matni = f"""
🚚 <b>YANGI YUK E'LONI</b> 🚚

📍 <b>Qayerdan:</b> {data['qayerdan']}
📍 <b>Qayerga:</b> {data['qayerga']}
🚛 <b>Transport:</b> {data['transport']}
📦 <b>Yuk turi:</b> {data['yuk_turi']}
💰 <b>Narxi:</b> {data['narx']} so'm

📱 <b>Bog'lanish uchun:</b>{username}
📞 {data['telefon']}
"""
        
        # Admin ID from environment variable
        ADMIN_ID = os.getenv("ADMIN_ID")
        if not ADMIN_ID:
            raise ValueError("ADMIN_ID not found in environment variables")

        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{callback.from_user.id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{callback.from_user.id}")
            ]
        ])

        # Send message to admin
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Yangi e'lon tasdiqlash uchun:\n\n{elon_matni}",
            reply_markup=admin_keyboard,
            parse_mode=ParseMode.HTML
        )

        # Notify user
        await callback.message.answer(
            "✅ E'loningiz admin tekshiruvi uchun yuborildi. Tasdiqlangandan so'ng kanalga joylanadi.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📝 E'lon berish")]],
                resize_keyboard=True
            )
        )

        await state.clear()
        await callback.answer()

    except ValueError as ve:
        logging.error(f"Environment xatolik: {str(ve)}")
        await callback.message.answer("⚠️ Tizim sozlamalarida xatolik. Admin bilan bog'laning.")
    except Exception as e:
        logging.error(f"Xatolik: {str(e)}")
        await callback.message.answer("❌ Xatolik yuz berdi. Iltimos qayta urinib ko'ring.")
        await state.clear()
        await callback.answer()






@dp.callback_query(lambda c: c.data.startswith('approve_'))
async def approve_post(callback: types.CallbackQuery):
    try:
        # Admin ID tekshirish
        if str(callback.from_user.id) != "816849899":
            await callback.answer("Siz admin emassiz!", show_alert=True)
            return
        
        # User ID ni olish
        user_id = callback.data.split('_')[1]
        
        # E'lon matnini olish
        elon_matni = callback.message.text.replace("Yangi e'lon tasdiqlash uchun:\n\n", "")
        
        # E'lon oxiriga kanal havolasi va reklama matni qo'shish
        footer_text = """

🚛 <b>Yuk tashish xizmati kerakmi?</b>
📢 <b>Bizning kanalga qo'shiling:</b> @logisticaUzbekiston

"""
        full_text = f"{elon_matni}\n{footer_text}"
        
        # Kanalga yuborish va xabar ID sini saqlash
        kanal_xabar = await bot.send_message(
            chat_id=CHANNEL_ID, 
            text=full_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🗑 E'lonni o'chirish", callback_data=f"delete_{user_id}_{callback.message.message_id}")
            ]])
        )
        
        # Admin xabarini yangilash
        await callback.message.edit_text(
            f"{elon_matni}\n\n✅ E'lon tasdiqlandi va kanalga joylandi!",
            parse_mode=ParseMode.HTML
        )
        
        # Foydalanuvchiga xabar yuborish
        await bot.send_message(
            chat_id=user_id, 
            text=f"✅ Sizning e'loningiz tasdiqlandi va kanalga joylandi!\n\nE'lon ID: {kanal_xabar.message_id}"
        )
        
        await callback.answer("E'lon tasdiqlandi!", show_alert=True)
        
    except Exception as e:
        logging.error(f"Approve xatolik: {str(e)}")
        await callback.answer("⚠️ Xatolik yuz berdi", show_alert=True)







# Yangi handler qo'shamiz e'lonni o'chirish uchun
@dp.callback_query(lambda c: c.data.startswith('delete_'))
async def delete_post(callback: types.CallbackQuery):
    try:
        # Ma'lumotlarni ajratib olish
        _, user_id, admin_msg_id = callback.data.split('_')
        
        # Faqat e'lon egasi o'chira oladi
        if str(callback.from_user.id) != user_id:
            await callback.answer("❌ Siz faqat o'zingizning e'loningizni o'chira olasiz!", show_alert=True)
            return
        
        # E'lonni o'chirish
        try:
            await callback.message.delete()
            await callback.answer("✅ E'lon muvaffaqiyatli o'chirildi!", show_alert=True)
            
        except Exception as e:
            logging.error(f"E'lonni o'chirishda xatolik: {str(e)}")
            await callback.answer("❌ E'lonni o'chirishda xatolik yuz berdi", show_alert=True)
            
    except Exception as e:
        logging.error(f"Delete xatolik: {str(e)}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)@dp.callback_query(lambda c: c.data.startswith('reject_'))
async def reject_post(callback: types.CallbackQuery):
    if str(callback.from_user.id) != 816849899:
        return
    
    user_id = callback.data.split('_')[1]
    await callback.message.edit_text(f"{callback.message.text}\n\n❌ E'lon rad etildi!")
    await bot.send_message(chat_id=user_id, text="❌ Sizning e'loningiz rad etildi.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())