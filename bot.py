from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
import openai
from pydub import AudioSegment

# keys
OPENAI_API_KEY = "sk-proj-xx"
TELEGRAM_BOT_TOKEN = "xx"
client = OpenAI(api_key=OPENAI_API_KEY)
openai.api_key = OPENAI_API_KEY

# chat history for every user
chat_history = {}

# startng command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    chat_history[chat_id] = []
    await update.message.reply_text("Hi! I'm chatGPT, ask me something.")

#  text message handling
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # enter your telegram username here to be in whitelist
    if user.username not in ["TELEGRAM_USERNAME"]:
        await update.message.reply_text("You are not whitelisted, sorry")
        return

    chat_id = update.message.chat_id
    user_message = update.message.text

    chat_history.setdefault(chat_id, []).append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            # chat gpt model
            model="gpt-4-turbo",
            messages=chat_history[chat_id],
        )

        reply = response.choices[0].message.content
        chat_history[chat_id].append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("Error")
        print("OpenAI Error:", e)

# voice message handling
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id
# enter your telegram username here to be in whitelist
    if user.username not in ["TELEGRAM_USERNAME"]:
        await update.message.reply_text("You are not whitelisted, sorry")
        return

    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)

        ogg_path = f"voice_{chat_id}.ogg"
        mp3_path = f"voice_{chat_id}.mp3"

        await file.download_to_drive(ogg_path)
        AudioSegment.from_file(ogg_path).export(mp3_path, format="mp3")

        with open(mp3_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        user_message = transcript.text

        chat_history.setdefault(chat_id, []).append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            #chat gpt model
            model="gpt-4-turbo",
            messages=chat_history[chat_id],
        )

        reply = response.choices[0].message.content
        chat_history[chat_id].append({"role": "assistant", "content": reply})

        await update.message.reply_text(f"You said: {user_message}\n\n {reply}")

    except Exception as e:
        await update.message.reply_text("Eroor during voice message recognition")
        print("Voice message error:", e)

# bot setting up and start
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot started.")
app.run_polling()
