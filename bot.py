import os
import asyncio
from aiogram import Bot, Dispatcher, types

# Проверка типа базы
USE_POSTGRES = bool(os.getenv("DATABASE_URL"))

if USE_POSTGRES:
    import asyncpg
else:
    import aiosqlite

# Настройки из переменных окружения
API_TOKEN = "8344456246:AAGa-Hy4zOOzoBJdIeJ2JxmdTzbMwE3v9yo"
CHANNEL_USERNAME = "@m_kapusssta"  # e.g. @mychannel
BONUS_TEXT = os.getenv("BONUS_TEXT", "🎁 Твой бонус: BONU$25")

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)


# ====== DB ИНИЦИАЛИЗАЦИЯ ======
async def init_db():
    if USE_POSTGRES:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY
            )
        """)
        await conn.close()
    else:
        async with aiosqlite.connect("users.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
            await db.commit()


async def has_user(user_id):
    if USE_POSTGRES:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        row = await conn.fetchrow("SELECT 1 FROM users WHERE user_id=$1", user_id)
        await conn.close()
        return bool(row)
    else:
        async with aiosqlite.connect("users.db") as db:
            async with db.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)) as cur:
                return bool(await cur.fetchone())


async def add_user(user_id):
    if USE_POSTGRES:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        await conn.execute(
            "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING", user_id
        )
        await conn.close()
    else:
        async with aiosqlite.connect("users.db") as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()


# ====== ЛОГИКА ПРОВЕРКИ ======
async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="📢 Подписаться",
            url=f"https://t.me/{m_kapusssta.lstrip('@')}"
        ),
        types.InlineKeyboardButton(
            text="✅ Проверить подписку", callback_data="check_sub"
        )
    )
   await message.answer(
    """Привет! 🔥 Остался один шаг до твоего модного апгрейда.

Подписка на @m_kapussta — это как подписка на стильную телепортацию:
🔸 Новинки, которые не доживают до вечера
🔸 Скидки, которые не светятся в рекламе
🔸 И вайбы, которые не продаются — только передаются

Нажми «Проверить подписку» — и получи секретный промокод, который работает как ключ к закрытому гардеробу.

⏳ Таймер тикает. Стиль не ждёт.""",
    reply_markup=kb
)


@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_subscription(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    if await is_subscribed(user_id):
        if await has_user(user_id):
            await cb.message.answer("✅ Ты уже получил бонус!")
        else:
            await add_user(user_id)
            await cb.message.answer(BONUS_TEXT)
    else:
        await cb.message.answer("❌ Похоже, ты ещё не подписался.")


async def main():
    await init_db()
    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
