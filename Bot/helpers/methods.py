from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Bot import db, bot

order_states = {'active': {'button': 'Mark as Prepared',
                           'callback': 'prepared',
                           'caption': """<b>Cheese Burger</b> is being prepared ... 🫕

Order ID ▪️ #O00012
Quantity ▪️ 2
Order State  ▪️ preparing

📌 <b><i>Once Order got finished mark it as prepared using below button.</i></b>"""},
                'prepared': {'button': 'Mark as Picked',
                             'callback': 'completed',
                             'caption': """<i><b>2 Cheese Burger</b> have been prepared.</i>

Order ID ▪️ #O00012
Quantity ▪️ 2
Order State  ▪️ prepared

📌 <b><i>Bicycle 🚲  is on the way to your restaurant, please mark this order as Picked once it got picked.</i></b>"""},
                'completed': {'button': '',
                              'callback': '',
                              'caption': """<b>This order have been marked us completed and picked</b>

Order ID ▪️ #O00012
Quantity ▪️ 2
Order State  ▪️ completed"""},
                'declined': {'button': '',
                             'callback': '',
                             'caption': """<b>This order is declined</b>

Order ID ▪️ #O00012
Quantity ▪️ 2
Order State  ▪️ declined"""}}


def order_manipulator(order_id, current: str, previous: str, restaurant_id, first_time: bool = False, ):
    """a function to manipulate orders from restaurants between 3 states:-
    active, prepared and completed orders"""

    orders = db.child("restaurants").child(restaurant_id).get().val()
    if not first_time:
        ord_obj = orders['orders'][previous]
        ord_obj.remove(order_id)
        db.child("restaurants").child(restaurant_id).child('orders').update(
            {previous: 0 if len(ord_obj) == 0 else ord_obj})
    if current == 'completed':
        db.child("restaurants").child(restaurant_id).update({'total': orders['total']+198})
    if orders['orders'][current] == 0:
        db.child("restaurants").child(restaurant_id).child('orders').update({current: [order_id]})
    elif isinstance(orders['orders'][current], list):
        ord_obj = orders['orders'][current]
        ord_obj.append(order_id)
        db.child("restaurants").child(restaurant_id).child('orders').update(
            {current: 0 if len(ord_obj) == 0 else ord_obj})


async def order_constructor(message: types.Message, restaurant_id):
    mes_type = message.text.split(" ")[0].lower()
    orders = db.child("restaurants").child(restaurant_id).get().val()['orders']
    if orders[mes_type] == 0:
        await message.answer(f"There is no {mes_type} order right now.")
    elif isinstance(orders[mes_type], list):
        for order_id in orders[mes_type]:
            order = db.child("orders").child(order_id).get().val()
            await bot.send_photo(
                message.from_user.id,
                order['photo'],
                order_states[mes_type]['caption'],
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(
                        order_states[mes_type]['button'],
                        callback_data=f'{order_states[mes_type]["callback"]}_order_O00012_{restaurant_id}'),
                    InlineKeyboardButton("Close", callback_data='close_order')
                ),
                parse_mode='HTML'
            )


async def dashboard_constructor(message: types.Message, restaurant_id):
    restaurant = db.child("restaurants").child(restaurant_id).get().val()
    text = f"""🔱 <u><b>{restaurant['name']}</b></u> 🔱

       👇<b> Restaurant Summary </b>👇

💰Total Earning: {restaurant['total']}Birr
👨‍🍳Total Completed : {0 if isinstance(restaurant['orders']['completed'], int)
    else len(restaurant['orders']['completed'])} Order(s) 
🫕Total Declined: {0 if isinstance(restaurant['orders']['declined'], int)
    else len(restaurant['orders']['declined'])} Order(s)

       <b>🆔 : {restaurant_id}</b>"""
    await bot.send_photo(
        message.from_user.id,
        restaurant['photo'],
        caption=text,
        parse_mode="HTML"
    )
