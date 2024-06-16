import requests
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

from scripts.text_to_text import query_gpt

# Токен вашего бота
TOKEN = 'YouToken'
API_URL = 'http://127.0.0.1:8000/api/'
IMG_FOLDER = 'img/'
MUSEUM_IMG = 'museum.jpg'
ADMIN_CHAT_ID = 'YouChatID'


async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [KeyboardButton("Задать вопрос")],
        [KeyboardButton("Новости")],
        [KeyboardButton("Экспонаты")],
        [KeyboardButton("О музее")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Пожалуйста, выберите опцию:', reply_markup=reply_markup)


def get_news():
    response = requests.get(API_URL + 'posts/')
    if response.status_code == 200:
        news_list = response.json()
        return news_list
    return []


def get_exhibits():
    response = requests.get(API_URL + 'exhibits/')
    if response.status_code == 200:
        exhibits_list = response.json()
        return exhibits_list
    return []


def get_about_info() -> str:
    response = requests.get(API_URL + 'about/')
    if response.status_code == 200:
        about_info = response.json()
        return about_info['description']
    return "Не удалось получить информацию о музее."


async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text

    if context.user_data.get('ASKING_QUESTION'):
        user_question = update.message.text
        response_text = await answer_question(user_question, context)
        await update.message.reply_text(response_text)
        context.user_data.pop('ASKING_QUESTION')
    else:
        if text == "Задать вопрос":
            await update.message.reply_text("Пожалуйста, задайте ваш вопрос:")
            context.user_data['ASKING_QUESTION'] = True
        elif text == "Новости":
            context.user_data['news_index'] = 0
            await send_news(update, context)
        elif text == "Экспонаты":
            context.user_data['exhibit_index'] = 0
            await send_exhibit(update, context)
        elif text == "О музее":
            await send_about_info(update, context)
        elif text == "Следующая новость":
            await send_next_news(update, context)
        elif text == "Следующий экспонат":
            await send_next_exhibit(update, context)
        elif text == "Вернуться в меню":
            await start(update, context)
        else:
            await update.message.reply_text('Пожалуйста, используйте кнопки для взаимодействия с ботом.')


async def send_news(update: Update, context: CallbackContext) -> None:
    news_list = get_news()
    if not news_list:
        await update.message.reply_text("Нет доступных новостей.")
        return

    news_index = context.user_data.get('news_index', 0)
    if news_index >= len(news_list):
        await update.message.reply_text("Больше нет новостей.")
        return

    news = news_list[news_index]
    title = news['title']
    content = news['content']
    img_filename = news['img']
    img_path = os.path.join(IMG_FOLDER, f"{img_filename}.jpg")

    news_text = f"{title}:\n{content}"

    keyboard = [
        [KeyboardButton("Следующая новость"), KeyboardButton("Вернуться в меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if os.path.exists(img_path):
        with open(img_path, 'rb') as img_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(img_file), caption=news_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(news_text, reply_markup=reply_markup)


async def send_next_news(update: Update, context: CallbackContext) -> None:
    context.user_data['news_index'] += 1
    await send_news(update, context)


async def send_exhibit(update: Update, context: CallbackContext) -> None:
    exhibits_list = get_exhibits()
    if not exhibits_list:
        await update.message.reply_text("Нет доступных экспонатов.")
        return

    exhibit_index = context.user_data.get('exhibit_index', 0)
    if exhibit_index >= len(exhibits_list):
        await update.message.reply_text("Больше нет экспонатов.")
        return

    exhibit = exhibits_list[exhibit_index]
    title = exhibit['title']
    content = exhibit['text']
    img_filename = exhibit['img']
    img_path = os.path.join(IMG_FOLDER, f"{img_filename}.jpg")

    exhibit_text = f"{title}:\n{content}"

    keyboard = [
        [KeyboardButton("Следующий экспонат"), KeyboardButton("Вернуться в меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if img_filename and os.path.exists(img_path):
        with open(img_path, 'rb') as img_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(img_file), caption=exhibit_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(exhibit_text, reply_markup=reply_markup)


async def send_next_exhibit(update: Update, context: CallbackContext) -> None:
    context.user_data['exhibit_index'] += 1
    await send_exhibit(update, context)


async def send_about_info(update: Update, context: CallbackContext) -> None:
    about_info = get_about_info()
    img_path = os.path.join(IMG_FOLDER, MUSEUM_IMG)

    if os.path.exists(img_path):
        with open(img_path, 'rb') as img_file:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(img_file), caption=about_info)
    else:
        await update.message.reply_text(about_info)


async def answer_question(user_question: str, context: CallbackContext) -> str:
    question_response = requests.get(API_URL + 'questions/')
    if question_response.status_code == 200:
        questions = question_response.json()
        matching_question = next((q for q in questions if q['question_text'].lower() == user_question.lower()), None)
        if matching_question:
            answer_id = matching_question['answer']
            answer_response = requests.get(API_URL + f'answers/{answer_id}/')
            if answer_response.status_code == 200:
                answer = answer_response.json()
                return answer['answer_text']

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Не нашлось ответа на вопрос: {user_question}")
    gpt_response = ask_gpt(user_question)
    return gpt_response


def ask_gpt(question: str) -> str:
    return query_gpt(question)


def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == '__main__':
    main()
