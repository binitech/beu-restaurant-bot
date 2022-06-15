from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import ChatNotFound

from Bot import db, dp, bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


class RestRegistrationForm(StatesGroup):
    phone = State()
    name = State()
    user_id = State()
    photo = State()


class FakeOrderState(StatesGroup):
    rest_id = State()


@dp.message_handler(Text(equals='/adminPanel'))
async def admin_panel_handler(message: types.Message):
    text = """.                  Admin Panel
    
📌 To register new restaurant click <b>🍽 Register Restaurant 🍽</b>.

📌 To send fake order to a restaurant click <b>🔗 Fake Order 🔗</b>"""
    await message.answer(text,
                         reply_markup=ReplyKeyboardMarkup(
                             resize_keyboard=True, keyboard=[
                                 ['🍽 Register Restaurant 🍽'], ['🔗 Fake Order 🔗'], ['Exit Panel'], []]
                         ),
                         parse_mode='HTML')


cancel_button = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[['❌ Cancel'], []])
skip_button = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[['Skip↪️'], []])


@dp.message_handler(Text(equals='🍽 Register Restaurant 🍽'))
async def register_rest_handler(message: types.Message):
    text = "\n\n<b>Enter phone number of the Restaurant.</b>\nIt should include country code.\n<i>Example: " \
           "251912345678</i>\n\nClick <b>❌ Cancel</b> to stop registration process."
    await message.answer(text,
                         reply_markup=cancel_button,
                         parse_mode='HTML')
    await RestRegistrationForm.phone.set()


@dp.message_handler(state=RestRegistrationForm.phone)
async def register_phone(message: types.Message, state: FSMContext):
    if message.text == '❌ Cancel':
        await message.answer("Process canceled")
        await state.finish()
        await admin_panel_handler(message)
        return
    if not message.text.isnumeric():
        await message.answer("Invalid Phone number, Enter again.")
        return
    async with state.proxy() as data:
        data['phone'] = message.text
    text = "<b>Phone number Saved ✅</b>\n\n<b>Enter the name of the restaurant.🙂</b>" \
           "\n\nClick <b>❌ Cancel</b> to stop registration process."
    await message.answer(text,
                         reply_markup=cancel_button,
                         parse_mode='HTML')
    await RestRegistrationForm.next()


@dp.message_handler(state=RestRegistrationForm.name)
async def register_name(message: types.Message, state: FSMContext):
    if message.text == '❌ Cancel':
        await message.answer("Process canceled")
        await state.finish()
        await admin_panel_handler(message)
        return
    async with state.proxy() as data:
        data['name'] = message.text
    text = "<b>Name Saved ✅</b>\n\n<i>Enter Restaurant owner\'s Telegram user-Id or you can forward one of their " \
           "telegram message, I will extract Id from it😉</i>" \
           "\n\n<b>This is used to send order notifications by the user-Id of Restaurant.</b>"
    await message.answer(text,
                         reply_markup=cancel_button,
                         parse_mode='HTML')
    await RestRegistrationForm.next()


@dp.message_handler(state=RestRegistrationForm.user_id)
async def register_user_id(message: types.Message, state: FSMContext):
    if message.text == '❌ Cancel':
        await message.answer("Process canceled")
        await state.finish()
        await admin_panel_handler(message)
        return
    async with state.proxy() as data:
        if message.is_forward():
            data['user_id'] = message.forward_from.id
        else:
            data['user_id'] = message.text
    text = "<b>User-Id Saved ✅</b>\n\nNow send me restaurant\'s photo, this will be used on Restaurant Dashboard." \
           "\n\nOR click <b>Skip↪️</b> and default photo will be settle."
    await message.answer(text,
                         reply_markup=skip_button,
                         parse_mode='HTML')
    await RestRegistrationForm.next()


@dp.message_handler(state=RestRegistrationForm.photo, content_types=types.ContentTypes.ANY)
async def register_photo(message: types.Message, state: FSMContext):
    if message.text == '❌ Cancel':
        await message.answer("Process canceled")
        await state.finish()
        await admin_panel_handler(message)
        return
    async with state.proxy() as data:
        if message.text == 'Skip↪️':
            data['photo'] = 'AgACAgQAAxkBAAEQU6BiqbxFQJvpl_TqynQRUrEwZFB4AwACtLoxG2p4SVHiYCNRYmeKdwEAAwIAA3kAAyQE'
        elif message.photo:
            data['photo'] = message.photo[-1].file_id
        else:
            await message.answer("Invalid Photo please send again.")
            return
    db_data = {data['phone']: {
        'name': data['name'],
        'orders': {
            "active": 0,
            "completed": 0,
            "declined": 0,
            "prepared": 0
        },
        'user_id': int(data['user_id']),
        'photo': data['photo'],
        'total': 0
    }}
    db.child("restaurants").update(db_data)
    await message.answer("Restaurant registered successfully.")
    await state.finish()
    await admin_panel_handler(message)


@dp.message_handler(Text(equals='🔗 Fake Order 🔗'))
async def fake_order_handler(message: types.Message):
    restaurants = db.child('restaurants').get().val()
    button = ReplyKeyboardMarkup(resize_keyboard=True)
    for rest in list(restaurants):
        button.add(KeyboardButton(rest))
    await message.answer("⏳ We are about to send fake order\nSelect restaurant below.",
                         reply_markup=button)
    await FakeOrderState.rest_id.set()


@dp.message_handler(state=FakeOrderState.rest_id)
async def fake_order(message: types.Message, state: FSMContext):
    restaurants = db.child('restaurants').child(message.text).get().val()
    if not message.text.isnumeric():
        await message.answer("Wrong entry, select only from below buttons.")
        return
    try:
        await bot.send_photo(
            restaurants['user_id'],
            "AgACAgUAAxkBAAEJUeJipcwGZOeruyHpUsWh4tWuu8r6pwACXrIxG3L2uVSobHm4Xf92gwEAAwIAA3kAAyQE",
            'New Order 🔔\n\nOrder detail:\n     2 - Cheese Burger\n\nOrder ID:\n    #00123212',
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("✅ Accept", callback_data=f'accept_order_O00012_{message.text}'),
                InlineKeyboardButton('❌ Decline', callback_data=f'decline_order_O00012_{message.text}')
            )
        )
        await message.answer("Sent Fake order to restaurant successfully.")
    except ChatNotFound:
        await message.answer("<b>The restaurant\'s telegram id is incorrect, or they should interact with the bot from "
                             "their account first.</b>", parse_mode='HTML')

    await state.finish()
    await admin_panel_handler(message)
