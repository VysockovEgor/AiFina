import base64
import json
import re
import time
import telebot
import mimetypes
from extractive_summarization import text_to_pdf
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import parsing
import textSpeach
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from Recommender import BookRecommender
from liderbord import *
import asyncio
import requests
from OpenAI_Connected import generate
from keys import BOT_KEY
bot = telebot.TeleBot(BOT_KEY)

recommender = BookRecommender()
images = {}
AllStages = {}
UsersOuts = {}
Books = {}
AllSearchInfo = {}
engine = create_engine("sqlite:///chat_history.db")
SessionLocal = sessionmaker(bind=engine)
BASE_URL = "http://127.0.0.1:8000"

def button_back(b2=None):
    markBack = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if b2 is not None:
        for i in b2:
            markBack.add(i)

    btn1 = types.KeyboardButton("⬅Назад⬅")
    markBack.add(btn1)
    return markBack

async def print_text(response, chat_id, markup, type_res, stage_now):
    if response.status_code == 200:
        m = None
        m1 = bot.send_message(chat_id, f"Ваше сообщение обрабатывается, ожидайте")
        m2 = bot.send_message(chat_id, "⌛")
        text_for_pdf = ''
        if stage_now == 'BookReq':
            words, rang, users = get_user_rating('@'+bot.get_chat_member(chat_id, chat_id).user.username)
            mes = ('<a href="http://127.0.0.1:8000">LiderBord\n</a>'+generate(
                f"Представь себя в роли случайного героя книги <b>{Books[chat_id][0]}</b>. Напиши поздравление и слова поддержки в 1 предложение для пользователя, который прочитал уже <b>{words}</b> слов. Укажи, что он находится на <b>{rang}</b> месте среди <b>{users}</b> участников. Сохрани стиль, тон и манеру речи этого героя. Вставь эмодзи, который соответствует этому персонажу, чтобы подчеркнуть его характер. Заверши сообщение подписью, указывающей, что поздравление исходит от имени данного героя И выдели числовые данные меткой <b></b>. "))
            bot.send_message(chat_id, f"<blockquote>{mes}</blockquote>", parse_mode='HTML', reply_markup=markup)
        for line in response.iter_lines(decode_unicode=True):
            if line.strip():
                if AllStages[int(chat_id)][-1] != stage_now: return
                data = json.loads(line)
                if m1 is not None:
                    bot.delete_message(chat_id, m1.message_id)
                    bot.delete_message(chat_id, m2.message_id)
                    m1=None
                if data.get("summary"):
                    update_words_read('@'+bot.get_chat_member(chat_id, chat_id).user.username, len(data.get("summary").split()))
                    if type_res=='text':
                        bot.send_message(chat_id, data.get("summary"), reply_markup=markup)
                    elif type_res=='audio':
                        bot.send_audio(chat_id, textSpeach.get_speech(data.get("summary")),
                                       reply_markup=markup,
                                       title='Ваше сообщение')
                    elif type_res=='pdf':
                        text_for_pdf+=data.get("summary")
                        if data.get("last"):
                            bot.send_document(chat_id, text_to_pdf(text_for_pdf), visible_file_name='Ваше сообщение' + '.pdf',
                                              reply_markup=markup)

                if data.get("last") and m is None:
                    with open('p.gif', 'rb') as f:
                        m = bot.send_animation(chat_id, f)
                if data.get("image"):
                    print(data.get("image"))
                    bot.edit_message_media(chat_id=chat_id, message_id=m.message_id,
                                           media=types.InputMediaPhoto(base64.b64decode(data.get("image"))))

    else:
        print("Ошибка:", response.status_code, response.text)

@bot.message_handler(commands=['start'])
def start(message):
    global AllStages, UsersOuts, images
    images[message.chat.id] = None
    if message.chat.id not in UsersOuts:
        requests.post(f"{BASE_URL}/settings/", json={'promt': [str(message.chat.id), '']})
        UsersOuts[message.chat.id] = 'Text'
    AllStages[message.chat.id] = [None, 'StartMenu']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn0 = types.KeyboardButton("⚙Настройки⚙")  # new
    btn1 = types.KeyboardButton("📖Ввести название книги📖")
    btn2 = types.KeyboardButton("📂Отправить файл📂")
    btn3 = types.KeyboardButton("✍Отправить текст сообщением✍")
    markup.add(btn1, btn2, btn3, btn0)  # new
    bot.send_message(message.chat.id,
                     f'Привет, {message.from_user.first_name}. \n Я бот-помошник для работы с большим объемом текста. Я могу сжать книгу или любой текст!',
                     reply_markup=markup)

def escape_markdown_v2(text):
    # Список всех специальных символов для MarkdownV2, кроме вертикальной черты и переноса строки
    special_chars = r"([\\*_\[\]()~`>#+\-=.!])"
    # Экранируем специальные символы
    escaped_text = re.sub(special_chars, r'\\\1', text)
    # Заменяем двойные кавычки на экранированные
    escaped_text = escaped_text.replace('"', '\\"')
    return escaped_text
@bot.message_handler(content_types=['text'])
def echo_message(message):
    global AllStages, AllSearchInfo

    if AllStages[message.chat.id][-1] == 'StartMenu':
        AllStages[message.chat.id][0] = 'StartMenu'
        if message.text == '⚙Настройки⚙':  # new
            AllStages[message.chat.id][-1] = 'Settings'  # new
            btn0 = types.KeyboardButton("📝Параметры сжатия📝")  # new
            btn1 = types.KeyboardButton("📤Тип вывода📤")  # new
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?',
                             reply_markup=button_back().add(btn0, btn1))  # new
        elif message.text == '📖Ввести название книги📖':
            AllStages[message.chat.id][-1] = 'BookReq'
            bot.send_message(message.chat.id,
                             'Напишите название книги!\nЕсли не помните, можете написать часть, я постараюсь найти!',
                             reply_markup=button_back())
        elif message.text == '📂Отправить файл📂':
            AllStages[message.chat.id][-1] = 'FileReq'
            bot.send_message(message.chat.id, "Отправьте файл, который нужно сжать✍", reply_markup=button_back())
            # bot.send_message(message.chat.id, "Отправте свой файл в формате .docx или .txt📂", reply_markup=button_back())
        elif message.text == '✍Отправить текст сообщением✍':
            AllStages[message.chat.id][-1] = 'TextReq'
            bot.send_message(message.chat.id, "Введите текст, который нужно сжать✍", reply_markup=button_back())
            # bot.send_message(message.chat.id, "Введите текст✍", reply_markup=button_back())

    elif AllStages[message.chat.id][-1] == 'Settings':  # new
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][-1] = 'StartMenu'
            AllStages[message.chat.id][0] = 'Settings'
            start(message)
        elif message.text == '📝Параметры сжатия📝':
            bot.send_message(message.chat.id, 'Напишите параметры сжатия:', reply_markup=button_back())
            AllStages[message.chat.id][-1] = 'ExpParamT'
            AllStages[message.chat.id][0] = 'Settings'
        elif message.text == '📤Тип вывода📤':
            btn0 = types.KeyboardButton("📝Текстом в сообщении📝")  # new
            btn1 = types.KeyboardButton("📁PDF файлом📁")
            btn2 = types.KeyboardButton("🔈Голосовым сообщением🔈")
            bot.send_message(message.chat.id, 'Выберите тип выводимого файла:',
                             reply_markup=button_back().add(btn0, btn1, btn2))
            AllStages[message.chat.id][-1] = 'OutParamT'
            AllStages[message.chat.id][0] = 'Settings'

    elif AllStages[message.chat.id][-1] == 'BookReq':
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][0] = 'BookReq'
            AllStages[message.chat.id][-1] = 'StartMenu'
            start(message)
        elif message.text == '📖Задать вопрос по тексту📖':
            AllStages[message.chat.id][0] = 'BookReq'
            AllStages[message.chat.id][-1] = 'Discus'
            bot.send_message(message.chat.id, 'Какой вопрос вы хотели бы задать?', reply_markup=button_back())
        elif message.text == '📖Сгенерировать тест по тексту📖':
            AllStages[message.chat.id][0] = 'BookReq'
            AllStages[message.chat.id][-1] = 'Test'
            response = requests.post(f"{BASE_URL}/test/", json={'id': str(message.chat.id)})
            data = response.json()  # Преобразуем ответ в словарь
            text = data['questions_and_answers']
            bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))

        elif 'Глава' in message.text:
            page_number = int(message.text.replace('Глава ', ''))
            tmp = Books[message.chat.id]
            tmp[2] = page_number
            callback_query(None, tmp)
        else:
            AllSearch = parsing.SearchProduct(message.text)
            if len(AllSearch) == 0:
                books = recommender.recommend_books(message.text)
                if books is not None:
                    for i in books:
                        name = i.split(';)')[0]
                        url = i.split(';)')[1]
                        AllSearch[name] = url
                    markupMessage = InlineKeyboardMarkup()
                    AllSearchInfo[message.chat.id] = {}
                    for key in AllSearch.keys():
                        AllSearchInfo[message.chat.id][key[:min(25, len(key))]] = [key, AllSearch[key], 1,
                                                                                   message.chat.id]
                        markupMessage.add(
                            InlineKeyboardButton(text=key, callback_data=key[:min(25, len(key))] + "%" + str(
                                message.chat.id)))
                    bot.send_message(message.chat.id, 'Что именно вы имели ввиду?', reply_markup=markupMessage)
                else:
                    bot.send_message(message.chat.id, 'По вашему запросу ничего не найдено:(')
            else:
                markupMessage = InlineKeyboardMarkup()
                AllSearchInfo[message.chat.id] = {}
                for key in AllSearch.keys():
                    AllSearchInfo[message.chat.id][key[:min(25, len(key))]] = [key, AllSearch[key], 1, message.chat.id]
                    markupMessage.add(InlineKeyboardButton(text=key, callback_data=key[:min(25, len(key))] + "%" + str(
                        message.chat.id)))
                bot.send_message(message.chat.id, 'Что именно вы имели ввиду?', reply_markup=markupMessage)
    elif AllStages[message.chat.id][-1] == 'FileReq':
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][0] = 'FileReq'
            AllStages[message.chat.id][-1] = 'StartMenu'
            start(message)
        elif message.text == '📖Сгенерировать тест по тексту📖':
            AllStages[message.chat.id][0] = 'BookReq'
            AllStages[message.chat.id][-1] = 'Test'
            response = requests.post(f"{BASE_URL}/test/", json={'id': str(message.chat.id)})
            data = response.json()  # Преобразуем ответ в словарь
            text = data['questions_and_answers']
            bot.send_message(message.chat.id, text, parse_mode="HTML",
                             reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))
    elif message.text == '📖Задать вопрос по тексту📖':
            AllStages[message.chat.id][0] = 'FileReq'
            AllStages[message.chat.id][-1] = 'Discus'
            bot.send_message(message.chat.id, 'Какой вопрос вы хотели бы задать?', reply_markup=button_back())
    elif AllStages[message.chat.id][-1] == 'TextReq':
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][0] = 'TextReq'
            AllStages[message.chat.id][-1] = 'StartMenu'
            start(message)
        elif message.text == '📖Сгенерировать тест по тексту📖':
            AllStages[message.chat.id][0] = 'BookReq'
            AllStages[message.chat.id][-1] = 'Test'
            response = requests.post(f"{BASE_URL}/test/", json={'id': str(message.chat.id)})
            data = response.json()  # Преобразуем ответ в словарь
            text = data['questions_and_answers']
            bot.send_message(message.chat.id, text, parse_mode="HTML",
                             reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))


        elif message.text == '📖Задать вопрос по тексту📖':
            AllStages[message.chat.id][0] = 'TextReq'
            AllStages[message.chat.id][-1] = 'Discus'
            bot.send_message(message.chat.id, 'Какой вопрос вы хотели бы задать?', reply_markup=button_back())
        else:
            chat_id = message.chat.id
            response = requests.post(f"{BASE_URL}/text/", json={'text':message.text, 'id':str(chat_id)}, stream=True)
            buttons = button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")).add(types.KeyboardButton("📖Сгенерировать тест по тексту📖"))
            if UsersOuts[message.chat.id] == 'Text':
                asyncio.run(print_text(response, chat_id, buttons,
                           'text', 'TextReq'))
            elif UsersOuts[message.chat.id] == 'Voice':
                asyncio.run(print_text(response, chat_id, buttons,
                           'audio', 'TextReq'))
            elif UsersOuts[message.chat.id] == 'File':
                asyncio.run(print_text(response, chat_id, buttons,
                           'pdf', 'TextReq'))


    elif AllStages[message.chat.id][-1] == 'Discus':
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][0] = 'Discus'
            AllStages[message.chat.id][-1] = 'StartMenu'
            start(message)
        elif message.text == '📖Сгенерировать тест по тексту📖':
            AllStages[message.chat.id][0] = 'Discus'
            AllStages[message.chat.id][-1] = 'Test'
            response = requests.post(f"{BASE_URL}/test/", json={'id': str(message.chat.id)})
            data = response.json()  # Преобразуем ответ в словарь
            text = data['questions_and_answers']
            bot.send_message(message.chat.id, text, parse_mode="HTML",
                             reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))


        else:
            res = requests.post(f"{BASE_URL}/answer/", json={'question':str(message.text), 'id':str(message.chat.id)})
            data = res.json()
            bot.send_message(message.chat.id,data['a'],
                             reply_markup=button_back().add(
                types.KeyboardButton("📖Сгенерировать тест по тексту📖")))
    elif AllStages[message.chat.id][-1] == 'Test':
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][0] = 'Test'
            AllStages[message.chat.id][-1] = 'StartMenu'
            start(message)
        elif message.text == '📖Задать вопрос по тексту📖':
            AllStages[message.chat.id][0] = 'Test'
            AllStages[message.chat.id][-1] = 'Discus'
            bot.send_message(message.chat.id, 'Какой вопрос вы хотели бы задать?', reply_markup=button_back())


    elif AllStages[message.chat.id][-1] == 'ExpParamT':  # new
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][-1] = 'StartMenu'
            AllStages[message.chat.id][-1] = 'ExpParamT'
            start(message)
        else:
            requests.post(f"{BASE_URL}/settings/", json={'promt': [str(message.chat.id), message.text]})
            AllStages[message.chat.id][-1] = 'Settings'  # new
            AllStages[message.chat.id][0] = 'ExpParamT'
            btn0 = types.KeyboardButton("📝Параметры сжатия📝")  # new
            btn1 = types.KeyboardButton("📤Тип вывода📤")  # new
            bot.send_message(message.chat.id, 'Параметры сжатия успешно установлены!')
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?',
                             reply_markup=button_back().add(btn0, btn1))  # new
    elif AllStages[message.chat.id][-1] == 'OutParamT':  # new
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][-1] = 'StartMenu'
            AllStages[message.chat.id][0] = 'OutParamT'
            start(message)
        elif message.text == "📝Текстом в сообщении📝":
            UsersOuts[message.chat.id] = 'Text'
            AllStages[message.chat.id][-1] = 'Settings'  # new
            AllStages[message.chat.id][0] = 'OutParamT'
            btn0 = types.KeyboardButton("📝Параметры сжатия📝")  # new
            btn1 = types.KeyboardButton("📤Тип вывода📤")  # new
            bot.send_message(message.chat.id, 'Тип выводимого файла успешно установлен!')
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?',
                             reply_markup=button_back().add(btn0, btn1))  # new
        elif message.text == '📁PDF файлом📁':
            UsersOuts[message.chat.id] = 'File'
            AllStages[message.chat.id][-1] = 'Settings'  # new
            AllStages[message.chat.id][0] = 'OutParamT'
            btn0 = types.KeyboardButton("📝Параметры сжатия📝")  # new
            btn1 = types.KeyboardButton("📤Тип вывода📤")  # new
            bot.send_message(message.chat.id, 'Тип выводимого файла успешно установлен!')
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?',
                             reply_markup=button_back().add(btn0, btn1))  # new
        elif message.text == '🔈Голосовым сообщением🔈':
            UsersOuts[message.chat.id] = 'Voice'
            AllStages[message.chat.id][-1] = 'Settings'  # new
            AllStages[message.chat.id][0] = 'OutParamT'
            btn0 = types.KeyboardButton("📝Параметры сжатия📝")  # new
            btn1 = types.KeyboardButton("📤Тип вывода📤")  # new
            bot.send_message(message.chat.id, 'Тип выводимого файла успешно установлен!')
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?',
                             reply_markup=button_back().add(btn0, btn1))  # new
        else:
            btn0 = types.KeyboardButton("📝Текстом в сообщении📝")  # new
            btn1 = types.KeyboardButton("📁PDF файлом📁")
            btn2 = types.KeyboardButton("🔈Голосовым сообщением🔈")
            bot.send_message(message.chat.id, "Такого типа вывода у нас нет :(",
                             reply_markup=button_back().add(btn0, btn1, btn2))


@bot.message_handler(content_types=['document'])
def get_file(message):
    global AllStages, images
    if AllStages[message.chat.id][-1] == 'FileReq':
        chat_id = message.chat.id

        if AllStages[int(chat_id)][-1] != 'FileReq': return
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name
        mime_type, _ = mimetypes.guess_type(file_name)
        if mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']:
            f = bot.download_file(file_info.file_path)
            response = requests.post(f"{BASE_URL}/file/", files={"file": f}, data={'id':str(chat_id)}, stream=True)
            buttons = button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")).add(
                types.KeyboardButton("📖Сгенерировать тест по тексту📖"))
            if UsersOuts[message.chat.id] == 'Text':
                asyncio.run(print_text(response, chat_id, buttons,
                           'text', 'FileReq'))
            elif UsersOuts[message.chat.id] == 'Voice':
                asyncio.run(print_text(response, chat_id, buttons,
                           'audio', 'FileReq'))
            elif UsersOuts[message.chat.id] == 'File':
                asyncio.run(print_text(response, chat_id, buttons,
                           'pdf', 'FileReq'))
        else:
            bot.send_message(message.chat.id,
                             "Неподдерживаемый тип файла. Пожалуйста, загрузите файл в формате .docx или .txt.")


@bot.callback_query_handler(func=lambda call: True)  # функция перехвата кнопок
def callback_query(call, ChoiceS=None):
    global AllStages, Books, AllSearchInfo
    try:
        if ChoiceS:
            ChoiceSearch = ChoiceS
            chat_id = int(ChoiceS[3])
        else:
            key_of_search, chat_id = call.data.split('%')
            chat_id = int(chat_id)
            ChoiceSearch = AllSearchInfo[chat_id][key_of_search]
        Books[int(ChoiceSearch[3])] = ChoiceSearch

        path_to_text = parsing.ParsingProductText(ChoiceSearch)
        with open(path_to_text, 'r', encoding='utf-8') as file:
            textBook = json.load(file)
            # print(textBook)
        txt = textBook['chapterText' + str(ChoiceSearch[2])]
        response = requests.post(f"{BASE_URL}/text/", json={'text': txt, 'id': str(chat_id)}, stream=True)
        if AllStages[int(ChoiceSearch[3])][-1] != 'BookReq': return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if ChoiceSearch[2] == 1:
            markup.row(types.KeyboardButton(f'Глава {ChoiceSearch[2] + 1}')).row(
                types.KeyboardButton("📖Задать вопрос по тексту📖")).row(types.KeyboardButton("📖Сгенерировать тест по тексту📖")).row(types.KeyboardButton("⬅Назад⬅"))
        elif ChoiceSearch[2] == textBook['count_all_pages']:
            markup.row(types.KeyboardButton(f'Глава {ChoiceSearch[2] - 1}')).row(
                types.KeyboardButton("📖Задать вопрос по тексту📖")).row(types.KeyboardButton("📖Сгенерировать тест по тексту📖")).row(types.KeyboardButton("⬅Назад⬅"))
        else:
            markup.row(types.KeyboardButton(f'Глава {ChoiceSearch[2] - 1}'),
                       types.KeyboardButton(f'Глава {ChoiceSearch[2] + 1}')).row(
                types.KeyboardButton("📖Задать вопрос по тексту📖"),types.KeyboardButton("📖Сгенерировать тест по тексту📖")).row(types.KeyboardButton("⬅Назад⬅"))


        if UsersOuts[chat_id] == 'Text':
            asyncio.run(print_text(response, chat_id, markup,
                       'text', 'BookReq'))
        elif UsersOuts[chat_id] == 'Voice':
            asyncio.run(print_text(response, chat_id, markup,
                       'audio', 'BookReq'))
        elif UsersOuts[chat_id] == 'File':
            asyncio.run(print_text(response, chat_id, markup,
                       'pdf', 'BookReq'))

    except ZeroDivisionError:  # Exception as e:
        # print(e)
        pass


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(5)
