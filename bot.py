import os
import sys
import random
import logging

# Setup logging FIRST
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get token
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not set!")
    sys.exit(1)

# Import telegram AFTER token check
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
except ImportError as e:
    logger.error(f"❌ Failed to import telegram: {e}")
    sys.exit(1)

# User data
users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            'balance': 100,
            'total_won': 0,
            'total_lost': 0,
            'games': 0
        }
    return users[user_id]

# ==================== COMMANDS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("🎰 Spin 10", callback_data="spin")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats"),
         InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    
    await update.message.reply_text(
        f"⚡ *RELOAD BOT* ⚡\n\n"
        f"Hi {user.first_name}!\n\n"
        f"💰 Balance: 100 coins\n"
        f"🎯 Bet: 1-100 coins\n\n"
        f"Use buttons or type commands!",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u = get_user(user_id)
    await update.message.reply_text(
        f"💰 *Balance*\n\n"
        f"Coins: {u['balance']}\n"
        f"Won: {u['total_won']}\n"
        f"Lost: {u['total_lost']}\n"
        f"Games: {u['games']}",
        parse_mode='Markdown'
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u = get_user(user_id)
    
    rate = 0
    if u['games'] > 0:
        total = u['total_won'] + u['total_lost']
        rate = (u['total_won'] / total * 100) if total > 0 else 0
    
    await update.message.reply_text(
        f"📊 *Stats*\n\n"
        f"Games: {u['games']}\n"
        f"Wins: {u['total_won']}\n"
        f"Losses: {u['total_lost']}\n"
        f"Win Rate: {rate:.1f}%\n"
        f"Balance: {u['balance']}",
        parse_mode='Markdown'
    )

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u = get_user(user_id)
    
    if not context.args:
        await update.message.reply_text(
            "❌ Use: `/bet 10`",
            parse_mode='Markdown'
        )
        return
    
    try:
        amount = int(context.args[0])
    except:
        await update.message.reply_text("❌ Enter a number!", parse_mode='Markdown')
        return
    
    if amount < 1 or amount > 100:
        await update.message.reply_text("❌ Bet 1-100 coins!", parse_mode='Markdown')
        return
    
    if amount > u['balance']:
        await update.message.reply_text(
            f"❌ Not enough! You have {u['balance']}",
            parse_mode='Markdown'
        )
        return
    
    win = random.random() > 0.5
    
    if win:
        u['balance'] += amount
        u['total_won'] += amount
        msg = f"🎉 *WIN!* +{amount}"
    else:
        u['balance'] -= amount
        u['total_lost'] += amount
        msg = f"😢 *LOSE!* -{amount}"
    
    u['games'] += 1
    
    await update.message.reply_text(
        f"{msg}\n\n💰 Balance: {u['balance']}",
        parse_mode='Markdown'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 *RELOAD BOT*\n\n"
        "/start - Menu\n"
        "/balance - Check\n"
        "/bet 10 - Bet\n"
        "/stats - Stats\n"
        "/help - This",
        parse_mode='Markdown'
    )

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    u = get_user(user_id)
    
    if query.data == "balance":
        await query.edit_message_text(
            f"💰 Balance: {u['balance']} coins",
            parse_mode='Markdown'
        )
    elif query.data == "spin":
        amount = 10
        if amount > u['balance']:
            await query.edit_message_text("❌ Not enough coins!", parse_mode='Markdown')
            return
        
        win = random.random() > 0.5
        if win:
            u['balance'] += amount
            u['total_won'] += amount
            msg = "🎉 WIN! +10"
        else:
            u['balance'] -= amount
            u['total_lost'] += amount
            msg = "😢 LOSE! -10"
        
        u['games'] += 1
        await query.edit_message_text(
            f"{msg}\n\n💰 Balance: {u['balance']}",
            parse_mode='Markdown'
        )
    elif query.data == "stats":
        rate = 0
        if u['games'] > 0:
            total = u['total_won'] + u['total_lost']
            rate = (u['total_won'] / total * 100) if total > 0 else 0
        
        await query.edit_message_text(
            f"📊 Games: {u['games']}\n"
            f"Wins: {u['total_won']}\n"
            f"Losses: {u['total_lost']}\n"
            f"Rate: {rate:.1f}%",
            parse_mode='Markdown'
        )
    elif query.data == "help":
        await query.edit_message_text(
            "/start - Menu\n/balance - Check\n/bet N - Bet\n/stats - Stats",
            parse_mode='Markdown'
        )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Use /help for commands",
        parse_mode='Markdown'
    )

# ==================== MAIN ====================

def main():
    logger.info("🚀 Starting RELOAD...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(None, echo))
    
    logger.info("✅ Bot running!")
    app.run_polling()

if __name__ == "__main__":
    main()
