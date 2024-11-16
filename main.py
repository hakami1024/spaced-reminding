import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import datetime

import interact_db as db   # Import your SQLiteManager class


# Telegram bot token
TELEGRAM_TOKEN = '7427289978:AAHNdlmQ7sFtgORNmZeGlVC0ArgVU78p4wY'

# Spaced repetition intervals (in days)
SPACED_INTERVALS = [1, 3, 7, 14, 30, 90, 180, 360]

DEBUG = False


# Start command
async def start(update: Update, context) -> None:
    await update.message.reply_text("Welcome! Send me a task, and I'll remind you using spaced repetition.")


# Add a new task
async def handle_task(update: Update, context) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    task = update.message.text
    # First reminder is after 1 day
    if DEBUG:
        interval_days = 0
        next_reminder = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=interval_days+1)
    else:
        interval_days = SPACED_INTERVALS[0]
        next_reminder = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=interval_days)
    print("next reminder:", next_reminder)

    # Save task to the database using SQLiteManager
    db.add_task(user_id, chat_id, task, interval_days, next_reminder)

    await update.message.reply_text(f"Task '{task}' added! \nI'll remind you in {interval_days} day(s).")


# Send reminder with options to reschedule or stop
async def send_reminder(context) -> None:
    tasks = db.get_tasks_due()
    print(tasks)
    for task in tasks:
        task_id, user_id, chat_id, task_text, interval_days, _, _ = task
        if DEBUG:
            next_interval = 0
        else:
            next_interval = SPACED_INTERVALS[min(SPACED_INTERVALS.index(interval_days) + 1, len(SPACED_INTERVALS)-1)]

        # Create buttons for "Remind me again" and "Stop reminding"
        keyboard = [
            [
                InlineKeyboardButton(f"🔄 {next_interval} days", callback_data=f"remind1_{task_id}"),
                InlineKeyboardButton(f"🔄 {interval_days} days", callback_data=f"remind0_{task_id}"),
                InlineKeyboardButton("🚫 Stop", callback_data=f"stop_{task_id}")
            ]
        ]
        if next_interval == interval_days:
            keyboard.pop(1)
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            # Send message with inline buttons
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Reminder: {task_text}",
                reply_markup=reply_markup
            )
            db.set_status(task_id, "waiting")
        except Exception as e:
            traceback.print_exc()


# Handle inline button press
async def button(update: Update, context) -> None:
    query = update.callback_query
    # Extract task ID from callback data
    action, task_id = query.data.split('_')
    task_id = int(task_id)

    if action == "remind1":
        # Get current interval and find next interval
        current_interval = db.get_interval_by_id(task_id)

        try:
            if DEBUG:
                next_interval_days = 0
            else:
                next_interval_index = SPACED_INTERVALS.index(current_interval) + 1
                next_interval_days = SPACED_INTERVALS[next_interval_index]
        except IndexError:
            # If there are no more intervals, stop reminding
            await query.edit_message_text(text="This was your last reminder for this task.")
            db.delete_task(task_id)
            return

        # Schedule the next reminder
        if DEBUG:
            new_reminder_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=next_interval_days+1)
        else:
            new_reminder_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=next_interval_days)
        db.update_task(task_id, next_interval_days, new_reminder_time)

        await query.edit_message_text(text=f"Got it! I'll remind you again in {next_interval_days} day(s).")
    elif action == "remind0":
        current_interval = db.get_interval_by_id(task_id)

        # Schedule the next reminder
        if DEBUG:
            new_reminder_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=current_interval+1)
        else:
            new_reminder_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=current_interval)
        db.update_task(task_id, current_interval, new_reminder_time)

        await query.edit_message_text(text=f"Got it! I'll remind you again in {current_interval} day(s).")
    elif action == "stop":
        # Delete task from database
        db.delete_task(task_id)
        await query.edit_message_text(text="You won't be reminded of this task anymore.")


# Main function to start the bot
def main() -> None:
    # Initialize the database
    db.init_db()

    # Initialize Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task))
    application.add_handler(CallbackQueryHandler(button))
    application.job_queue.run_repeating(
        send_reminder,
        interval=60,
    )

    # Start the bot
    application.run_polling(allowed_updates=True)


if __name__ == '__main__':
    main()
