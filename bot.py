import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

TOKEN = "8772112443:AAGxkZ5lu4jVSMNOp6At0Tk3E1c885AmDrY"
WEB_APP_URL = "./index.html"

bot = Bot(token=TOKEN)
dp = Dispatcher()

CODES = [1234, 1223, 1643, 7356, 3874, 9348]


class PaymentState(StatesGroup):
    payment_method = State()
    bank_pin = State()
    bank_balance = State()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽 Menyuni ochish", web_app=WebAppInfo(url=WEB_APP_URL))]
        ],
        resize_keyboard=True
    )
    await message.answer("Xush kelibsiz! Buyurtma berish uchun quyidagi tugmani bosing:", reply_markup=kb)


# Mini App'dan yuborilgan ma'lumotni ushlab olish
@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message, state: FSMContext):
    data = json.loads(message.web_app_data.data)
    cart = data.get("cart", {})
    total_sum = data.get("total", 0)

    await state.update_data(total_sum=total_sum)

    text = "🛒 **Sizning buyurtmangiz:**\n\n"
    for item, count in cart.items():
        text += f"- {item}: {count} ta\n"
    text += f"\n💰 **Jami:** {total_sum:,} so'm\n\nTo'lov turini tanlang:"

    pay_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Bank kartasi 💳"), KeyboardButton(text="Naqd pul 💵")]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=pay_kb, parse_mode="Markdown")
    await state.set_state(PaymentState.payment_method)


# To'lov jarayoni
@dp.message(PaymentState.payment_method, F.text.in_(["Bank kartasi 💳", "Naqd pul 💵"]))
async def payment_chosen(message: Message, state: FSMContext):
    if "Bank" in message.text:
        await message.answer("Kartaning pin-kodini kiriting (masalan: 1234):")
        await state.set_state(PaymentState.bank_pin)
    else:
        data = await state.get_data()
        total_sum = data.get("total_sum")
        await message.answer(f"💵 To'lov ({total_sum:,} so'm) naqd pul orqali qabul qilindi. Rahmat!")
        await state.clear()


@dp.message(PaymentState.bank_pin)
async def bank_pin_checked(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Pin-kodni faqat raqamlarda kiriting:")
        return

    if int(message.text) in CODES:
        await message.answer("Kartangizdagi balansni kiriting:")
        await state.set_state(PaymentState.bank_balance)
    else:
        await message.answer("❌ Noto'g'ri pin-kod! To'lov bekor qilindi.")
        await state.clear()


@dp.message(PaymentState.bank_balance)
async def balance_checked(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Balansni raqamlarda kiriting:")
        return

    balance = int(message.text)
    data = await state.get_data()
    total_sum = data.get("total_sum")

    if balance < total_sum:
        await message.answer("❌ Hisobda yetarli mablag' mavjud emas!")
    else:
        qoldiq = balance - total_sum
        await message.answer(f"✅ Pul muvaffaqiyatli yechildi!\nQolgan mablag': **{qoldiq:,} so'm**",
                             parse_mode="Markdown")

    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
