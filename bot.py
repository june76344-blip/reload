import logging
import sys
import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    sys.exit(1)

# User data (in-memory)
users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            'balance': 100,
            'total_won': 0,
            'total_lost': 0,
            'games_played': 0
        }
    return users[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("🎰 Spin", callback_data="spin")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats"),
         InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚡ *WELCOME TO RELOAD BOT!* ⚡\n\n"
        f"Hi {user.first_name}! I'm your gaming companion.\n\n"
        f"💰 Starting balance: 100 coins\n"
        f"🎯 Min bet: 1 coin\n"
        f"🎯 Max bet: 100 coins\n\n"
        f"Use the buttons below or type commands!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    await update.message.reply_text(
        f"💰 *Your Balance*\n\n"
        f"Balance: *{user['balance']} coins*\n"
        f"Total Won: *{user['total_won']}*\n"
        f"Total Lost: *{user['total_lost']}*\n"
        f"Games: *{user['games_played']}*",
        parse_mode='Markdown'
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    win_rate = 0
    if user['games_played'] > 0:
        total = user['total_won'] + user['total_lost']
        win_rate = (user['total_won'] / total * 100) if total > 0 else 0
    
    await update.message.reply_text(
        f"📊 *Your Stats*\n\n"
        f"Games Played: *{user['games_played']}*\n"
        f"Total Won: *{user['total_won']}*\n"
        f"Total Lost: *{user['total_lost']}*\n"
        f"Win Rate: *{win_rate:.1f}%*\n"
        f"Balance: *{user['balance']} coins*",
        parse_mode='Markdown'
    )

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify amount!\nExample: `/bet 10`",
            parse_mode='Markdown'
        )
        return
    
    try:
        amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount!", parse_mode='Markdown')
        return
    
    if amount < 1:
        await update.message.reply_text("❌ Minimum bet is 1 coin!", parse_mode='Markdown')
        return
    
    if amount > 100:
        await update.message.reply_text("❌ Maximum bet is 100 coins!", parse_mode='Markdown')
        return
    
    if amount > user['balance']:
        await update.message.reply_text(
            f"❌ Insufficient balance!\nYour balance: {user['balance']} coins",
            parse_mode='Markdown'
        )
        return
    
    win = random.random() > 0.5
    
    if win:
        user['balance'] += amount
        user['total_won'] += amount
        result = f"🎉 *YOU WIN!*\n+{amount} coins"
    else:
        user['balance'] -= amount
        user['total_lost'] += amount
        result = f"😢 *YOU LOSE!*\n-{amount} coins"
    
    user['games_played'] += 1
    
    await update.message.reply_text(
        f"{result}\n\n💰 New balance: {user['balance']} coins",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 *RELOAD BOT*\n\n"
        "/start - Main menu\n"
        "/balance - Check balance\n"
        "/bet <amount> - Place bet\n"
        "/stats - View stats\n"
        "/help - This message",
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    if query.data == "balance":
        await query.edit_message_text(
            f"💰 *Balance*\n\nBalance: {user['balance']} coins",
            parse_mode='Markdown'
        )
    elif query.data == "spin":
        amount = 10
        if amount > user['balance']:
            await query.edit_message_text("❌ Insufficient balance!", parse_mode='Markdown')
            return
        
        win = random.random() > 0.5
        if win:
            user['balance'] += amount
            user['total_won'] += amount
            result = f"🎉 WIN! +{amount} coins"
        else:
            user['balance'] -= amount
            user['total_lost'] += amount
            result = f"😢 LOSE! -{amount} coins"
        
        user['games_played'] += 1
        await query.edit_message_text(
            f"{result}\n\n💰 Balance: {user['balance']} coins",
            parse_mode='Markdown'
        )
    elif query.data == "stats":
        win_rate = 0
        if user['games_played'] > 0:
            total = user['total_won'] + user['total_lost']
            win_rate = (user['total_won'] / total * 100) if total > 0 else 0
        
        await query.edit_message_text(
            f"📊 *Stats*\n\nGames: {user['games_played']}\nWon: {user['total_won']}\nLost: {user['total_lost']}\nWin Rate: {win_rate:.1f}%",
            parse_mode='Markdown'
        )
    elif query.data == "help":
        await query.edit_message_text(
            "Commands:\n/start - Menu\n/balance - Balance\n/bet <amount> - Bet\n/stats - Stats\n/help - Help",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Use /help to see available commands!",
        parse_mode='Markdown'
    )

def main():
    try:
        logger.info("🚀 Starting RELOAD Bot...")
        app = Application.builder().token(BOT_TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("balance", balance))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("bet", bet))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Bot is running!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
