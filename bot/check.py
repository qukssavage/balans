import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN

async def check():
    bot = Bot(TELEGRAM_BOT_TOKEN)
    me = await bot.get_me()
    print('can_read_all_group_messages:', me.can_read_all_group_messages)
    print('supports_inline_queries:', me.supports_inline_queries)

asyncio.run(check())