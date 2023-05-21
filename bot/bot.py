import asyncio
import os
import sys

# Import necessary modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from unidecode import unidecode
import logging
import bot_module
from backend import backend_module, api
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

# Ignore warning messages related to CallbackQueryHandler
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s',
    encoding='utf-8'
)

# Define stages
START_ROUTES, GET_USERNAME_NEW_USER, GET_PASSWORD_NEW_USER, GET_USERNAME_UPDATE_USER, GET_PASSWORD_UPDATE_USER, \
    ADD_USER, UPDATE_USER, UPDATE_CREDIT, UPDATE_MENU, CREATED, CHANGE_USERNAME, CHANGE_PASSWORD, END_ROUTES = range(13)

# Define callback data
keys = {
    "USER_INFO": "USER_INFO",
    "RESERVED": "RESERVED",
    "MENU": "MENU",
    "CREDIT": "CREDIT",
    "AUTO_RESERVE": "AUTO_RESERVE",
    "BEST_FOODS": "BEST_FOODS",
    "START": "START",
    "UPDATE_USER_INFO": "UPDATE_USER_INFO",
    "UPDATE_CREDIT": "UPDATE_CREDIT",
    "MOST_RESERVED_FOOD": "MOST_RESERVED_FOOD"
}

# Define data
data = {
    "PHOTO_FILE_ID": "AgACAgQAAxkBAAOcZGhuaB0PTsUqdhhnU6uWzSidOC4AAiK9MRsS_CBT-MsStWPtmdIBAAMCAAN5AAMvBA",
    "PHOTO_CAPTION": "🍽 برنامه غذای هفته 16 آموزشی"
}


# Function to add user to the bot's database
async def add_user_to_bot_database(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Add user to the database using bot_module
        bot_module.add_user_to_bot_database(
            update.message.from_user.id,
            context.user_data["username"],
            context.user_data["password"]
        )
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(text="""ساخت حساب شما با مشکل روبرو شد، با پشتیبانی تماس بگیرید""")
        return START_ROUTES
    await update.message.reply_text(text="""حساب شما با موفقیت ساخته شد!""")
    await start(update, context)
    return START_ROUTES


# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    if bot_module.check_user_exist(user.id):
        logging.info("User %s(%i) started the conversation.", user.first_name, user.id)
        # Create the inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("اطلاعات کاربر", callback_data=f"{keys['USER_INFO']}"),
                InlineKeyboardButton("نمایش رزرو ها", callback_data=f"{keys['RESERVED']}"),
            ],
            [
                InlineKeyboardButton("منو", callback_data=f"{keys['MENU']}"),
                InlineKeyboardButton("اعتبار باقی مانده", callback_data=f"{keys['CREDIT']}"),
            ],
            [InlineKeyboardButton("لیست غذاهای مورد علاقه", callback_data=f"{keys['MOST_RESERVED_FOOD']}")],
            [InlineKeyboardButton("رزرو غذا خودکار", callback_data=f"{keys['AUTO_RESERVE']}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = """به ربات سفارش غذای خودکار سلف شاهرود خوش آمدید
        این ربات بر اساس بیشترین انتخاب های قبلی شما اقدام به رزرو غذا برای هفته جدید میکند"""
        await update.message.reply_text(msg, reply_markup=reply_markup)
        return START_ROUTES
    else:
        await update.message.reply_text(text="""شما تا به حال در ربات ثبت نام نداشته اید.
نام کاربری خود را وارد کنید:""")
        return GET_USERNAME_NEW_USER


# Rollback to start state
async def rollback_start(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    user = update.callback_query.from_user
    logging.info("User %s(%i) back to start state.", user.first_name, user.id)
    keyboard = [
        [
            InlineKeyboardButton("اطلاعات کاربر", callback_data=f"{keys['USER_INFO']}"),
            InlineKeyboardButton("نمایش رزرو ها", callback_data=f"{keys['RESERVED']}"),
        ],
        [
            InlineKeyboardButton("منو", callback_data=f"{keys['MENU']}"),
            InlineKeyboardButton("اعتبار باقی مانده", callback_data=f"{keys['CREDIT']}"),
        ],
        [InlineKeyboardButton("لیست غذاهای مورد علاقه", callback_data=f"{keys['MOST_RESERVED_FOOD']}")],
        [InlineKeyboardButton("رزرو غذا خودکار", callback_data=f"{keys['AUTO_RESERVE']}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = """به ربات سفارش غذای خودکار سلف شاهرود خوش آمدید"""
    try:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup)
    except:
        await update.callback_query.delete_message()
    return START_ROUTES


# Function to get username from new user
async def get_username_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = unidecode(update.message.text.strip())
    context.user_data["username"] = username
    await update.message.reply_text(text="""گذرواژه خود را وارد کنید:""")
    return GET_PASSWORD_NEW_USER


# Function to get password from new user
async def get_password_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = unidecode(update.message.text.strip())
    context.user_data["password"] = password
    try:
        bot_module.add_user_to_bot_database(update.message.from_user.id, context.user_data["username"],
                                            context.user_data["password"])
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(text="""ساخت حساب شما با مشکل روبرو شد، با پشتیبانی تماس بگیرید""")
        return START_ROUTES
    await update.message.reply_text(text="""حساب شما با موفقیت ساخته شد!""")
    await start(update, context)
    return START_ROUTES


# Function to get username from user for updating user info
async def get_username_update_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    username = unidecode(update.message.text.strip())
    context.user_data["username"] = username
    user_id = update.message.from_user.id
    print(username, user_id)
    if backend_module.check_user_exist_bot_table(user_id):
        await update.message.reply_text(text="""گذرواژه خود را وارد کنید:""")
        return GET_PASSWORD_UPDATE_USER
    else:
        msg = """
        در حال حاضر قادر به ثبت اطلاعات شما نیستیم. لطفا کمی صبر کنید و با پشتیبانی تماس بگیرید
        """
        await update.message.reply_text(text=msg)
        return START_ROUTES


# Function to get password from user for updating user info
async def get_password_update_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = unidecode(update.message.text.strip())
    context.user_data["password"] = password
    try:
        bot_module.update_user_info_in_data(update.message.from_user.id, context.user_data["username"],
                                            context.user_data["password"])
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(text="""ساخت حساب شما با مشکل روبرو شد، با پشتیبانی تماس بگیرید""")
        return START_ROUTES
    await update.message.reply_text(text="""حساب شما با موفقیت بروزرسانی شد!""")
    await start(update, context)
    return START_ROUTES


async def update_user_info(update: Update, context: CallbackContext):
    """
    Update user information handler function.
    Asks the user for a new username and returns the next conversation state.
    """
    query = update.callback_query
    await query.answer()
    msg = """
    ویرایش نام کاربری و رمز ورود
    نام کاربری جدید خود را وارد کنید:
    """
    await query.message.reply_text(text=msg)
    return GET_USERNAME_UPDATE_USER


async def get_user_info(update: Update, context: CallbackContext):
    """
    Get user information handler function.
    Retrieves the user's username and password and displays them with options to update or return to the main menu.
    """
    query = update.callback_query
    await query.answer()
    user = backend_module.User(query.from_user.id)
    username = user.username
    password = user.password
    msg = f"""
    نام کاربری:  {username}
    رمزعبور:  {password}
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "تغییر رمز عبور و نام کاربری", callback_data=keys['UPDATE_USER_INFO']
            )
        ],
        [
            InlineKeyboardButton(
                "بازگشت", callback_data=keys['START'])
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=msg, reply_markup=reply_markup)


async def show_menu(update: Update, context: CallbackContext):
    """
    Show menu handler function.
    Displays the menu with options to return to the main menu.
    """
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton(
                "بازگشت", callback_data=keys['START']),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_photo(photo=data['PHOTO_FILE_ID'], caption=data['PHOTO_CAPTION'],
                                    reply_markup=reply_markup)


async def get_photo_file_id(channel_username: str, message_id: int, context: CallbackContext) -> str:
    """
    Get photo file ID handler function.
    Retrieves the file ID of a photo message from a given channel and message ID.
    """
    chat = await context.bot.get_chat(channel_username)
    message = await context.bot.get_message(chat.id, message_id)
    photo = message.photo[-1]  # get the highest resolution photo
    return photo.file_id


async def show_reserved(update: Update, context: CallbackContext):
    """
    Show reserved handler function.
    Displays the reserved food and options to return to the main menu.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "بازگشت", callback_data=keys['START']),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="در حال انجام درخواست شما هستیم لطفا صبر کنید...")
    result = await api.main(query.from_user.id, False)
    meal_names = {"صبحانه": "breakfast", "نهار": "lunch", "شام": "dinner"}
    day_strings = [f"{day['day']}: \n      {day.get('error', '') or format_food(day['food'])}\n" for day in result]
    for meal_name in meal_names:
        day_strings = [day_string.replace(meal_names[meal_name], meal_name) for day_string in day_strings]
    msg = ''.join(day_strings)
    await query.edit_message_text(text=msg, reply_markup=reply_markup)


async def show_credit(update: Update, context: CallbackContext):
    """
    Show credit handler function.
    Displays the user's credit and options to update or return to the main menu.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "بروزرسانی موجودی", callback_data=keys["UPDATE_CREDIT"]),
        ],
        [
            InlineKeyboardButton(
                "بازگشت", callback_data=keys['START']),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.answer()
    credit = backend_module.get_credit(query.from_user.id)
    msg = f"""
    آخرین موجودی شما: {credit} تومان
    """
    await query.edit_message_text(text=msg, reply_markup=reply_markup)


async def update_credit(update: Update, context: CallbackContext):
    """
    Update credit handler function.
    Updates the user's credit and displays the updated credit with options to update or return to the main menu.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "بروزرسانی موجودی", callback_data=keys["UPDATE_CREDIT"]),
        ],
        [
            InlineKeyboardButton(
                "بازگشت", callback_data=keys['START']),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="در حال رزرو کردن وعده ها هستیم لطفا صبر کنید...")

    def run_update():
        return backend_module.update_credit(query.from_user.id)

    credit = await asyncio.get_running_loop().run_in_executor(None, run_update)
    msg = f"""
        موجودی بروزشده شما: {credit} تومان
        """
    await query.edit_message_text(text=msg, reply_markup=reply_markup)


async def auto_reserve_food(update: Update, context: CallbackContext):
    """
    Auto reserve food handler function.
    Automatically reserves food for the user and displays the reserved food with options to return to the main menu.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "بازگشت", callback_data=keys['START']),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="در حال رزرو کردن وعده ها هستیم لطفا صبر کنید...")
    result = await api.main(query.from_user.id, True)
    meal_names = {"صبحانه": "breakfast", "نهار": "lunch", "شام": "dinner"}
    day_strings = [f"{day['day']}: \n      {day.get('error', '') or format_food(day['food'])}\n" for day in result]
    for meal_name in meal_names:
        day_strings = [day_string.replace(meal_names[meal_name], meal_name) for day_string in day_strings]
    msg = ''.join(day_strings)
    await query.edit_message_text(text=msg, reply_markup=reply_markup)


def format_food(food):
    """
    Formats the food dictionary into a string representation.
    """
    return '\n      '.join([f"{meal}: ( {food[meal]} )" for meal in food])


async def update_menu_pic(update: Update, context: CallbackContext):
    """
    Update menu photo handler function.
    Updates the menu photo and displays the updated photo.
    """
    admin_user_id = int()  # You should enter your admin user id here
    if update.message.from_user.id == admin_user_id:
        await update.message.reply_text(text="hello Admin, Send me the new MENU...")
        return UPDATE_MENU
    else:
        await update.message.reply_text(text="You are not admitted as ADMIN don't try to hack me :)")
        return START_ROUTES


async def menu_updating(update: Update, context: CallbackContext):
    """
    Menu updating handler function.
    Updates the menu photo and caption.
    """
    photo = update.message.photo[-1]
    data['PHOTO_FILE_ID'] = photo.file_id
    data['PHOTO_CAPTION'] = update.message.caption
    await update.message.reply_text(text="Menu photo updated successfully")
    await update.message.reply_photo(photo=data['PHOTO_FILE_ID'], caption=data['PHOTO_CAPTION'])
    print(data)


async def show_most_reserved_food(update: Update, context: CallbackContext):
    """
    Show most reserved food handler function.
    Displays the most reserved food by the user and options to return to the main menu.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "بازگشت", callback_data=keys['START']),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="در حال انجام درخواست شما هستیم لطفا صبر کنید...")
    result = backend_module.get_most_reserved_food(query.from_user.id)
    msg = "بیشترین غذا های رزرو شده شما \n"
    for i, (item, count) in enumerate(result, 1):
        msg += f"{i}. {item}: {count}بار\n"
    await query.edit_message_text(text=msg, reply_markup=reply_markup)


def main() -> None:
    """
    Main function to run the Telegram bot application.
    """
    application = Application.builder().token('numbernumbernumber:stringstringstring').build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("update_credit", update_credit),
            CommandHandler("show_reserved", show_reserved),
            CommandHandler("show_menu", show_menu),
            CommandHandler("show_credit", show_credit),
            CommandHandler("auto_reserve_food", auto_reserve_food),
            CommandHandler("show_most_reserved_food", show_most_reserved_food),
        ],
        states={
            START_ROUTES: [
                CallbackQueryHandler(start, pattern=f"^{keys['START']}$")
            ],
            GET_USERNAME_NEW_USER: [
                CallbackQueryHandler(get_username_new_user, pattern=f"^{keys['USER_INFO']}$")
            ],
            GET_PASSWORD_NEW_USER: [
                MessageHandler(filters.TEXT, get_password_new_user)
            ],
            GET_USERNAME_UPDATE_USER: [
                CallbackQueryHandler(update_user_info, pattern=f"^{keys['UPDATE_USER_INFO']}$")
            ],
            GET_PASSWORD_UPDATE_USER: [
                MessageHandler(filters.TEXT, get_password_update_user)
            ],
            UPDATE_MENU: [
                MessageHandler(filters.PHOTO, menu_updating)
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handlers([conv_handler])

    application.run()


if __name__ == "__main__":
    main()
