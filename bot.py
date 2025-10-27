import os
TOKEN = os.getenv("8241501478:AAE02YhGZAOtdcSz80fYGx1e0vyIwdWPZeE")

import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime

DB_FILE = "reservations.db"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            date TEXT,
            start TEXT,
            end TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_FILE)

# Reserve command
async def reserve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /reserve YYYY-MM-DD HH:MM HH:MM")
        return

    date, start, end = context.args
    user = update.effective_user.first_name

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM reservations WHERE date=? AND NOT (? <= start OR ? >= end)",
        (date, end, start)
    )
    conflict = c.fetchone()

    if conflict:
        await update.message.reply_text("❌ Time slot already reserved.")
    else:
        c.execute("INSERT INTO reservations (user, date, start, end) VALUES (?, ?, ?, ?)",
                  (user, date, start, end))
        conn.commit()
        await update.message.reply_text(f"✅ Reserved on {date} from {start} to {end} for {user}.")
    conn.close()

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /cancel YYYY-MM-DD HH:MM")
        return

    date, start = context.args
    user = update.effective_user.first_name
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM reservations WHERE date=? AND start=? AND user=?", (date, start, user))
    conn.commit()

    if c.rowcount > 0:
        await update.message.reply_text("🗑️ Reservation canceled.")
    else:
        await update.message.reply_text("Reservation not found or not yours.")
    conn.close()

# Schedule command
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user, date, start, end FROM reservations ORDER BY date, start")
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No reservations yet.")
        return

    msg = "📅 *Current Reservations:*\n"
    for r in rows:
        msg += f"{r[1]} {r[2]}–{r[3]} — {r[0]}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# Myreservations command
async def my_reservations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT date, start, end FROM reservations WHERE user=? ORDER BY date, start", (user,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("You have no reservations.")
        return

    msg = f"📅 *{user}'s Reservations:*\n"
    for r in rows:
        msg += f"{r[0]} {r[1]}–{r[2]}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/reserve YYYY-MM-DD HH:MM HH:MM — Make a reservation\n"
        "/cancel YYYY-MM-DD HH:MM — Cancel your reservation\n"
        "/schedule — View all reservations\n"
        "/myreservations — View your reservations"
    )

def main():
    init_db()
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("reserve", reserve))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("myreservations", my_reservations))
    app.add_handler(CommandHandler("help", help_command))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

