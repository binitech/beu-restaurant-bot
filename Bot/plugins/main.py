from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from Bot import dp, db
from aiogram import types
from Bot.helpers.methods import order_manipulator, order_constructor, dashboard_constructor, order_states


@dp.message_handler(Text(equals=['/start', 'Exit Panel']))
async def start_handler(message: types.Message):
    text = f"""Hey, *{message.from_user.first_name}! 👋*

` * This is restaurant order management simulation bot. * `

📌 To continue as a restaurant owner please *Share Contact ☎️* using the below button.

📌 To continue as *Super Admin👲 *please click the below command.
/adminPanel"""
    await message.answer(
        text,
        parse_mode="MARKDOWN",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton(
                "Share Contact ☎",
                request_contact=True,
            ))
    )


@dp.message_handler(content_types=types.ContentTypes.CONTACT)
async def phone_handler(message: types.Message):
    if message.contact:
        restaurant = db.child("restaurants").child(int(message.contact.phone_number)).get().val()
        if restaurant is None:
            await message.answer(
                "<b><i>It seems like this phone number is not registered as a restaurant, please visit the /adminPanel "
                "to register it.😀</i></b> ",
                parse_mode='HTML'
            )
            return
        await message.answer(
            f"🍬 {restaurant['name']} 🍬",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[['Dashboard'], ['Active Orders', 'Prepared Orders'], ['Completed Orders', 'Declined Orders'],
                          ['Sign Out'],
                          []],
                resize_keyboard=True
            )
        )


@dp.callback_query_handler(Text(startswith='accept_order'))
async def accept_order_handler(query: types.InlineQuery):
    order = query.data.split('_')
    order_manipulator(order[-2], 'active', 'active', order[-1], first_time=True)
    await query.message.edit_caption(
        order_states['active']['caption'],
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(order_states['active']['button'], callback_data=f'prepared_order_O00012_{order[-1]}'),
            InlineKeyboardButton("Close", callback_data='close_order')
        ),
        parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='decline_order'))
async def decline_order_handler(query: types.InlineQuery):
    order = query.data.split('_')
    order_manipulator(order[-2], 'declined', 'declined', order[-1], first_time=True)
    await query.message.edit_caption(
        order_states[order[0]]['caption'],
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Close", callback_data='close_order')
        ),
        parse_mode='HTML')


@dp.callback_query_handler(Text(startswith='prepared_order'))
async def prepared_order_handler(query: types.InlineQuery):
    order = query.data.split('_')
    order_manipulator(order[-2], 'prepared', 'active', order[-1])
    await query.message.edit_caption(
        order_states[order[0]]['caption'],
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(order_states[order[0]]['button'], callback_data=f'completed_order_O00012_{order[-1]}'),
            InlineKeyboardButton("Close", callback_data='close_order')
        ),
        parse_mode='HTML')


@dp.callback_query_handler(Text(startswith='completed_order'))
async def picked_order_handler(query: types.InlineQuery):
    order = query.data.split('_')
    order_manipulator(order[-2], 'completed', 'prepared', order[-1])
    await query.message.edit_caption(
        order_states[order[0]]['caption'],
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Close", callback_data='close_order')
        ),
        parse_mode='HTML'
    )


@dp.callback_query_handler(Text(startswith='close_order'))
async def close_order_handler(query: types.CallbackQuery):
    await query.answer("Closed", show_alert=True)
    await query.message.delete()


@dp.message_handler(
    Text(equals=['Dashboard', 'Active Orders', 'Prepared Orders', 'Declined Orders', 'Completed Orders', 'Sign Out']))
async def restaurant_order_handler(message: types.Message):
    phone = db.child('restaurants').order_by_child('user_id').equal_to(message.from_user.id).get().val()
    if message.text == 'Sign Out':
        await start_handler(message)
        return
    elif message.text == 'Dashboard':
        await dashboard_constructor(message, list(phone)[0])
    else:
        await order_constructor(message, list(phone)[0])
