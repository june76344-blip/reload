#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN not found in environment variables!")
    sys.exit(1)

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== USER DATA (in-memory, resets on restart) ====================
users = {}

def get_user(user_id):
    """Get or create user data"""
    if user_id not in users:
        users[user_id] = {
            'balance': 100,
            'total_won': 0,
            'total_lost': 0,
            'games_played': 0,
            'joined_date': datetime.now().isoformat()
        }
    return users[user_id]

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with menu"""
    user = update.effective_user
    user_id = str(user.id)
    
    # Initialize user
    get_user(user_id)
    
    # Create inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("🎰 Spin", callback_data="spin")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="stats"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
⚡ *WELCOME TO RELOAD BOT!* ⚡

Hi {user.first_name}! I'm your gaming and betting companion.

🎮 *Features:*
• Spin to win with real balance tracking
• 50/50 chance - double your bet!
• Track your wins, losses, and stats

💰 *Starting balance:* 100 coins
🎯 *Min bet:* 1 coin
🎯 *Max bet:* 100 coins

Use the buttons below or type commands!
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = """
🎮 *RELOAD BOT - Help*

*Commands:*
/start - Show main menu
/balance - Check your balance
/bet <amount> - Place a bet (50/50 win)
/stats - View your game statistics
/help - Show this help

*How to play:*
1. Type `/bet 10` to bet 10 coins
2. Win = get 2x your bet!
3. Lose = lose your bet

*Example:*
`/bet 25` - Bet 25 coins

⚠️ *Disclaimer:* For entertainment only!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user balance"""
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    balance_text = f"""
💰 *Your Balance*

━━━━━━━━━━━━━━━━━━
💵 Current Balance: *{user['balance']} coins*
━━━━━━━━━━━━━━━━━━
✅ Total Won: *{user['total_won']} coins*
❌ Total Lost: *{user['total_lost']} coins*
🎯 Games Played: *{user['games_played']}*
━━━━━━━━━━━━━━━━━━

🎯 Min bet: 1 coin
🎯 Max bet: 100 coins
"""
    await update.message.reply_text(balance_text, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    # Calculate win rate
    games = user['games_played']
    win_rate = 0
    if games > 0:
        win_rate = (user['total_won'] / (user['total_won'] + user['total_lost'])) * 100 if (user['total_won'] + user['total_lost']) > 0 else 0
    
    stats_text = f"""
📊 *Your Statistics*

━━━━━━━━━━━━━━━━━━
🎯 Games Played: *{games}*
✅ Wins: *{user['total_won']}*
❌ Losses: *{user['total_lost']}*
📈 Win Rate: *{win_rate:.1f}%*
💰 Current Balance: *{user['balance']}*
━━━━━━━━━━━━━━━━━━

📅 Joined: {user['joined_date'][:10]}
"""
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Place a bet"""
    import random
    
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    # Check if amount is provided
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify an amount!\n"
            "Example: `/bet 10`",
            parse_mode='Markdown'
        )
        return
    
    try:
        bet_amount = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount! Please enter a number.",
            parse_mode='Markdown'
        )
        return
    
    # Validate bet
    if bet_amount < 1:
        await update.message.reply_text(
            "❌ Minimum bet is 1 coin!",
            parse_mode='Markdown'
        )
        return
    
    if bet_amount > 100:
        await update.message.reply_text(
            "❌ Maximum bet is 100 coins!",
            parse_mode='Markdown'
        )
        return
    
    if bet_amount > user['balance']:
        await update.message.reply_text(
            f"❌ Insufficient balance!\n"
            f"Your balance: {user['balance']} coins\n"
            f"Bet: {bet_amount} coins",
            parse_mode='Markdown'
        )
        return
    
    # 50/50 chance
    win = random.random() > 0.5
    
    if win:
        win_amount = bet_amount * 2
        user['balance'] += bet_amount  # Net profit = bet amount
        user['total_won'] += bet_amount
        result_text = f"🎉 *YOU WIN!*\n\n"
        result_text += f"💰 Bet: {bet_amount} coins\n"
        result_text += f"💵 Win: {win_amount} coins\n"
        result_text += f"📈 Profit: +{bet_amount} coins\n\n"
        result_text += f"💰 New balance: {user['balance']} coins"
    else:
        user['balance'] -= bet_amount
        user['total_lost'] += bet_amount
        result_text = f"😢 *YOU LOSE!*\n\n"
        result_text += f"💰 Bet: {bet_amount} coins\n"
        result_text += f"📉 Loss: -{bet_amount} coins\n\n"
        result_text += f"💰 New balance: {user['balance']} coins"
    
    user['games_played'] += 1
    
    await update.message.reply_text(result_text, parse_mode='Markdown')

# ==================== CALLBACK HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    if query.data == "balance":
        await query.edit_message_text(
            f"💰 *Your Balance*\n\n"
            f"Current Balance: *{user['balance']} coins*\n"
            f"Total Won: *{user['total_won']} coins*\n"
            f"Total Lost: *{user['total_lost']} coins*",
            parse_mode='Markdown'
        )
    
    elif query.data == "spin":
        # Quick spin via button
        import random
        bet_amount = 10  # Default quick bet
        
        if bet_amount > user['balance']:
            await query.edit_message_text(
                f"❌ Insufficient balance!\n"
                f"Your balance: {user['balance']} coins\n"
                f"Try `/bet` command instead.",
                parse_mode='Markdown'
            )
            return
        
        win = random.random() > 0.5
        
        if win:
            user['balance'] += bet_amount
            user['total_won'] += bet_amount
            result = f"🎉 *YOU WIN!* +{bet_amount} coins"
        else:
            user['balance'] -= bet_amount
            user['total_lost'] += bet_amount
            result = f"😢 *YOU LOSE!* -{bet_amount} coins"
        
        user['games_played'] += 1
        
        await query.edit_message_text(
            f"{result}\n\n"
            f"💰 New balance: {user['balance']} coins\n\n"
            f"Use `/bet <amount>` to bet any amount!",
            parse_mode='Markdown'
        )
    
    elif query.data == "stats":
        games = user['games_played']
        win_rate = 0
        if games > 0:
            total = user['total_won'] + user['total_lost']
            win_rate = (user['total_won'] / total) * 100 if total > 0 else 0
        
        await query.edit_message_text(
            f"📊 *Your Stats*\n\n"
            f"Games: {games}\n"
            f"Wins: {user['total_won']}\n"
            f"Losses: {user['total_lost']}\n"
            f"Win Rate: {win_rate:.1f}%\n"
            f"Balance: {user['balance']} coins",
            parse_mode='Markdown'
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            "🎮 *RELOAD BOT Commands*\n\n"
            "/start - Main menu\n"
            "/balance - Check balance\n"
            "/bet <amount> - Place bet\n"
            "/stats - View statistics\n"
            "/help - Show this\n\n"
            "💡 Try `/bet 10` to start!",
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages"""
    await update.message.reply_text(
        "🤖 I didn't understand that.\n"
        "Try /help to see available commands!",
        parse_mode='Markdown'
    )

# ==================== MAIN FUNCTION ====================

def main():
    """Start the bot"""
    try:
        logger.info("🚀 Starting RELOAD Bot...")
        logger.info(f"🔑 Token: {BOT_TOKEN[:15]}...")
        
        # Create application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("balance", balance_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CommandHandler("bet", bet_command))
        
        # Callback handler for inline buttons
        app.add_handler(CallbackQueryHandler(button_callback))
        
        # Message handler
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start the bot
        logger.info("✅ Bot is running! Waiting for messages...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
