import os
from dotenv import load_dotenv
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import aiosqlite
import aiohttp
import datetime
from jose import jwt

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('TG_BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

BACKEND_URL = "http://127.0.0.1:8000"
ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID'))
DB_PATH = 'bot_users.db'

class UserStates(StatesGroup):
    waiting_for_imei = State()
    waiting_for_user_id_add = State()
    waiting_for_user_id_del = State()

async def clean_imei(text: str) -> str:
    text = text.lower()
    prefixes = ['imei:', 'imei', 'number:', 'number', 'code:', 'code', '#']
    for prefix in prefixes:
        text = text.replace(prefix, '')
    
    cleaned = ''.join(filter(str.isdigit, text))
    return cleaned

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS authorized_users
            (user_id INTEGER PRIMARY KEY, username TEXT, added_date TEXT)
        ''')
        await db.commit()

async def is_authorized(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            'SELECT 1 FROM authorized_users WHERE user_id = ?', 
            (user_id,)
        ) as cursor:
            return await cursor.fetchone() is not None

async def check_imei(imei: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{BACKEND_URL}/api/check-imei",
                params={"imei": imei},
                headers=headers
            ) as response:
                return await response.json()
        except aiohttp.ClientError as e:
            return {"error": str(e)}
        
async def get_token():
    secret_key = os.getenv('JWT_SECRET_KEY')
    payload = {
        "sub": "user",
        "exp": datetime.datetime.now() + datetime.timedelta(days=30)
    }
    token = jwt.encode(
        payload,
        secret_key,
        algorithm="HS256"
    )
    return token

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not await is_authorized(message.from_user.id):
        await message.reply("You are not authorized to use this bot. Please contact admin.")
        return
    
    help_text = (
        "Welcome! I can help you check IMEI numbers.\n\n"
        "You can send me an IMEI in any of these formats:\n"
        "• Just the number: 357369092971157\n"
        "• With IMEI prefix: IMEI: 357369092971157\n"
        "• With spaces or other separators: 35736-90929-71157\n\n"
        "I'll clean up the format and check it for you!"
    )
    await message.reply(help_text)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    if not await is_authorized(message.from_user.id):
        return
    
    help_text = (
        "📱 *IMEI Check Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "*IMEI Format:*\n"
        "• IMEI should be 15 digits\n"
        "• You can include spaces or separators\n"
        "• You can use prefixes like 'IMEI:'\n\n"
        "*Examples of valid input:*\n"
        "357369092971157\n"
        "IMEI: 357369092971157\n"
        "35736-90929-71157\n"
        "IMEI number: 357369092971157\n\n"
        "*Note:* I'll clean up the format automatically!"
    )
    await message.reply(help_text, parse_mode="Markdown")

@dp.message(Command("add_user"))
async def cmd_add_user(message: types.Message, state: FSMContext):
    # if message.from_user.id != ADMIN_ID:
    #     await message.reply("You are not authorized to add users.")
    #     return
    
    await message.reply("Please send the Telegram user ID you want to authorize.")
    await state.set_state(UserStates.waiting_for_user_id_add)

@dp.message(StateFilter(UserStates.waiting_for_user_id_add))
async def process_add_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                'INSERT OR REPLACE INTO authorized_users (user_id, added_date) VALUES (?, ?)',
                (user_id, datetime.datetime.now().isoformat())
            )
            await db.commit()
        await message.reply(f"User {user_id} has been authorized.")
    except ValueError:
        await message.reply("Invalid user ID. Please send a valid number.")
    except aiosqlite.Error as e:
        await message.reply(f"Database error: {str(e)}")
    finally:
        await state.clear()

@dp.message(Command("del_user"))
async def cmd_del_user(message: types.Message, state: FSMContext):
    # if message.from_user.id != ADMIN_ID:
    #     await message.reply("You are not authorized to remove users.")
    #     return
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT user_id FROM authorized_users') as cursor:
            users = await cursor.fetchall()
    
    if not users:
        await message.reply("No authorized users found.")
        return
    
    user_list = "\n".join([f"User ID: {user[0]}" for user in users])
    await message.reply(f"Current authorized users:\n{user_list}\n\nSend the user ID to remove.")
    await state.set_state(UserStates.waiting_for_user_id_del)

@dp.message(StateFilter(UserStates.waiting_for_user_id_del))
async def process_del_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('DELETE FROM authorized_users WHERE user_id = ?', (user_id,))
            await db.commit()
        await message.reply(f"User {user_id} has been removed from authorized users.")
    except ValueError:
        await message.reply("Invalid user ID. Please send a valid number.")
    except aiosqlite.Error as e:
        await message.reply(f"Database error: {str(e)}")
    finally:
        await state.clear()

@dp.message(F.text)
async def handle_imei(message: types.Message):
    if not await is_authorized(message.from_user.id):
        await message.reply("You are not authorized to use this bot. Please contact admin.")
        return

    original_text = message.text.strip()
    cleaned_imei = await clean_imei(original_text)
    
    if not cleaned_imei:
        await message.reply(
            "I couldn't find any numbers in your message.\n"
            "Please send me an IMEI number.\n"
            "Use /help to see example formats."
        )
        return
    
    processing_msg = await message.reply("🔍 Processing your request...\nPlease wait.")
    
    try:
        token = await get_token()
        if not token:
            await processing_msg.delete()
            await message.reply("Error: Could not get authorization token.")
            return

        result = await check_imei(cleaned_imei, token)
        
        await processing_msg.delete()
        
        if "error" in result:
            await message.reply(f"Error: {result['error']}")
            return
        
        if result["status"] == "invalid":
            await message.reply(
                f"❌ Invalid IMEI: {result['message']}\n\n"
                f"Original input: {original_text}\n"
                f"Cleaned number: {cleaned_imei}"
            )
            return
        
        details = result.get("details", {})
        properties = details.get("properties", {})
        
        purchase_date = properties.get("estPurchaseDate")
        if purchase_date:
            purchase_date = datetime.datetime.fromtimestamp(purchase_date).strftime("%Y-%m-%d")
        
        response = (
            f"✅ *IMEI Check Results*\n\n"
            f"IMEI: `{cleaned_imei}`\n"
            f"Original input: {original_text}\n\n"
            f"*Device Information:*\n"
            f"• Model: {properties.get('deviceName', 'N/A')}\n"
            f"• Serial Number: `{properties.get('serial', 'N/A')}`\n"
            f"• IMEI 2: `{properties.get('imei2', 'N/A')}`\n"
            f"• MEID: `{properties.get('meid', 'N/A')}`\n"
            f"• Network: {properties.get('network', 'N/A')}\n"
            f"• Est. Purchase Date: {purchase_date if purchase_date else 'N/A'}\n\n"
            f"*Status Information:*\n"
            f"• Block Status: {properties.get('usaBlockStatus', 'N/A')}\n"
            f"• Replaced: {'Yes' if properties.get('replaced') else 'No'}\n"
            f"• Demo Unit: {'Yes' if properties.get('demoUnit') else 'No'}\n\n"
            f"*Service Information:*\n"
            f"• Service: {details.get('service', {}).get('title', 'N/A')}\n"
            f"• Check ID: `{details.get('id', 'N/A')}`\n"
            f"• Processed: {datetime.datetime.fromtimestamp(details.get('processedAt', 0)).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        image_url = properties.get('image')
        if image_url:
            try:
                await message.reply_photo(
                    photo=image_url,
                    caption=response,
                    parse_mode="Markdown"
                )
            except Exception:
                await message.reply(
                    response,
                    parse_mode="Markdown"
                )
        else:
            await message.reply(
                response,
                parse_mode="Markdown"
            )
            
    except Exception as e:
        await processing_msg.delete()
        await message.reply(f"An error occurred: {str(e)}")
        

async def main():
    """Main function to run the bot"""
    await init_db()
    logging.info("Bot started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
