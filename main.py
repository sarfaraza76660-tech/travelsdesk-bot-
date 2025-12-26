import os, json, asyncio
from datetime import datetime
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import discord
from discord.ext import commands
import aiohttp

# Load secrets
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")

SERVICES = {
    "flights": "✈️ Flights",
    "hotels": "🏨 Hotels", 
    "theme_park": "🎫 Theme Park",
    "food": "🍔 Food & Catering",
    "excursions": "🌐 Excursions & Tours",
    "car_rentals": "🚗 Car Rentals",
    "international": "🌍 International Travel"
}

user_sessions = {}

async def start(update, context):
    keyboard = [[InlineKeyboardButton(v, callback_data=k)] for k, v in SERVICES.items()]
    await update.message.reply_text(
        "🌟 *Welcome to TravelsDesk Bot By Lizzux*\n\nChoose service:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def selected(update, context):
    query = update.callback_query
    await query.answer()
    user_sessions[query.from_user.id] = {"service": query.data}
    await query.edit_message_text("Step 1/5: *Your full name*:", parse_mode="Markdown")

async def handle_msg(update, context):
    user_id = update.from_user.id
    if user_id not in user_sessions:
        return
    
    session = user_sessions[user_id]
    if "name" not in session:
        session["name"] = update.message.text
        await update.message.reply_text("Step 2/5: *Email address*:", parse_mode="Markdown")
    elif "email" not in session:
        session["email"] = update.message.text
        await update.message.reply_text("Step 3/5: *Travel date (DD/MM/YYYY)*:", parse_mode="Markdown")
    elif "date" not in session:
        session["date"] = update.message.text
        await update.message.reply_text("Step 4/5: *Budget/Cost*:", parse_mode="Markdown")
    elif "cost" not in session:
        session["cost"] = update.message.text
        await update.message.reply_text("Step 5/5: *Additional details*:", parse_mode="Markdown")
    else:
        session["details"] = update.message.text
        
        # Send to Discord
        service_name = SERVICES[session["service"]]
        msg = f"**🎫 NEW TICKET**\n\n**Service:** {service_name}\n**Name:** {session['name']}\n**Email:** {session['email']}\n**Date:** {session['date']}\n**Budget:** {session['cost']}\n**Details:** {session['details']}\n**Telegram ID:** `{user_id}`"
        
        async with aiohttp.ClientSession() as s:
            await s.post(WEBHOOK, json={"content": msg})
        
        await update.message.reply_text("✅ *Ticket sent successfully!*\n\nOur team will contact you soon on Telegram.", parse_mode="Markdown")
        del user_sessions[user_id]

# Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def reply(ctx, user_id: int, *, message: str):
    await telegram_bot.send_message(chat_id=user_id, text=f"📩 *TravelsDesk:* {message}", parse_mode="Markdown")
    await ctx.send(f"✅ Sent to {user_id}")

telegram_bot = Bot(token=TOKEN)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(selected))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    await asyncio.gather(app.run_polling(), bot.start(DISCORD_TOKEN))

if __name__ == "__main__":
    asyncio.run(main())
      
