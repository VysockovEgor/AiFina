import telebot
import mimetypes
import threading
from files_reader import text_convert,text_to_pdf
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import parsing
import textSpeach
from giga_chat import Chatbot, Message
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from kandinsk import *
from docx import Document
bot = telebot.TeleBot('7478065724:AAFIGP8uvexUB4doSfSuOKpUQa7JAs5CkHY')
api = Text2ImageAPI('https://api-key.fusionbrain.ai/', 'FFF38A30E2CF342FB2285816955634BE',
                    '883274A123A24F113E0A512C0EA45FF6')
images={}
AllStages = {}
UsersPromts = {}
UsersOuts = {}
Books = {}
AllSearchInfo = {}
chatbot = Chatbot()
engine = create_engine("sqlite:///chat_history.db")
SessionLocal = sessionmaker(bind=engine)

def button_back(b2=None):
    markBack = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if b2 is not None:
        for i in b2:
            markBack.add(i)

    btn1 = types.KeyboardButton("⬅Назад⬅")
    markBack.add(btn1)
    return markBack
def send_image(id, text):
    global images
    images[id] = api.gen(text)

def clear_history_for_user(user_id):
    session = SessionLocal()
    try:
        session.query(Message).filter_by(user_id=user_id).delete()
        session.commit()
    except Exception as e:
        session.rollback()  # Откат транзакции в случае ошибки
        print(f"Error deleting messages for user {user_id}: {e}")
    finally:
        session.close()

@bot.message_handler(commands=['start'])
def start(message):
    global AllStages, UsersPromts, UsersOuts, images
    images[message.chat.id] = None

    clear_history_for_user(message.chat.id)
    if message.chat.id not in UsersPromts:
        UsersPromts[message.chat.id]=''
    if message.chat.id not in UsersOuts:
        UsersOuts[message.chat.id] = 'Text'
    AllStages[message.chat.id] = [None,'StartMenu']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn0 = types.KeyboardButton("⚙Настройки⚙") #new
    btn1 = types.KeyboardButton("📖Ввести название книги📖")
    btn2 = types.KeyboardButton("📂Отправить файл📂")
    btn3 = types.KeyboardButton("✍Отправить текст сообщением✍")
    markup.add(btn1, btn2, btn3, btn0) #new
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}. \n Я бот-помошник для работы с большим объемом текста. Я могу сжать книгу или любой текст!', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def echo_message(message):
    global AllStages, UsersPromts, AllSearchInfo

    if AllStages[message.chat.id][-1] == 'StartMenu':
        AllStages[message.chat.id][0] = 'StartMenu'
        if message.text == '⚙Настройки⚙': #new
            AllStages[message.chat.id][-1] = 'Settings' #new
            btn0 = types.KeyboardButton("📝Параметры сжатия📝") #new
            btn1 = types.KeyboardButton("📤Тип вывода📤") #new
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?', reply_markup=button_back().add(btn0, btn1)) #new
        elif message.text == '📖Ввести название книги📖':
            AllStages[message.chat.id][-1] = 'BookReq'
            bot.send_message(message.chat.id, 'Напишите название книги!\nЕсли не помните, можете написать часть, я постараюсь найти!', reply_markup=button_back())
        elif message.text == '📂Отправить файл📂':
            AllStages[message.chat.id][-1] = 'FileReq'
            bot.send_message(message.chat.id, "Отправьте файл, который нужно сжать✍", reply_markup=button_back())
            #bot.send_message(message.chat.id, "Отправте свой файл в формате .docx или .txt📂", reply_markup=button_back())
        elif message.text == '✍Отправить текст сообщением✍':
            AllStages[message.chat.id][-1] = 'TextReq'
            bot.send_message(message.chat.id, "Введите текст, который нужно сжать✍", reply_markup=button_back())
            #bot.send_message(message.chat.id, "Введите текст✍", reply_markup=button_back())
    elif AllStages[message.chat.id][-1] == 'Settings': #new
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][-1] = 'StartMenu'
            AllStages[message.chat.id][0] = 'Settings'
            chatbot.cancel_user_message(message.chat.id)
            start(message)
        elif message.text == '📝Параметры сжатия📝':
            bot.send_message(message.chat.id, 'Напишите параметры сжатия:', reply_markup=button_back())
            AllStages[message.chat.id][-1] = 'ExpParamT'
            AllStages[message.chat.id][0] = 'Settings'
        elif message.text == '📤Тип вывода📤':
            btn0 = types.KeyboardButton("📝Текстом в сообщении📝") #new
            btn1 = types.KeyboardButton("📁PDF файлом📁")
            btn2 = types.KeyboardButton("🔈Голосовым сообщением🔈")
            bot.send_message(message.chat.id, 'Выберите тип выводимого файла:', reply_markup=button_back().add(btn0, btn1, btn2))
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
        elif 'Страница' in message.text:
            page_number = int(message.text.replace('Страница ', ''))
            tmp = Books[message.chat.id]
            tmp[2] = page_number
            callback_query(None, tmp)
        else:
            AllSearch = parsing.SearchProduct(message.text)
            if len(AllSearch) == 0:
                bot.send_message(message.chat.id, 'По вашему запросу ничего не найдено:(')
            else:
                markupMessage = InlineKeyboardMarkup()
                AllSearchInfo[message.chat.id] = {}
                for key in AllSearch.keys():
                    AllSearchInfo[message.chat.id][key[:min(25, len(key))]] = [key, AllSearch[key], 1, message.chat.id]
                    markupMessage.add(InlineKeyboardButton(text=key, callback_data=key[:min(25, len(key))] + "%" + str(message.chat.id)))
                bot.send_message(message.chat.id, 'Что именно вы имели ввиду?', reply_markup=markupMessage)
    elif AllStages[message.chat.id][-1] == 'FileReq':
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][0] = 'FileReq'
            AllStages[message.chat.id][-1] = 'StartMenu'
            start(message)
        elif message.text == '📖Задать вопрос по тексту📖':
            AllStages[message.chat.id][0] = 'FileReq'
            AllStages[message.chat.id][-1] = 'Discus'
            bot.send_message(message.chat.id, 'Какой вопрос вы хотели бы задать?', reply_markup=button_back())
    elif AllStages[message.chat.id][-1] == 'TextReq':
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][0] = 'TextReq'
            AllStages[message.chat.id][-1] = 'StartMenu'
            chatbot.cancel_user_message(message.chat.id)
            start(message)
        elif message.text == '📖Задать вопрос по тексту📖':
            AllStages[message.chat.id][0] = 'TextReq'
            AllStages[message.chat.id][-1] = 'Discus'
            bot.send_message(message.chat.id, 'Какой вопрос вы хотели бы задать?', reply_markup=button_back())
        else:
            chat_id = message.chat.id
            mdel = bot.send_message(message.chat.id, f"Ваше сообщение обрабатывается, ожидайте")
            chat_id = message.chat.id
            msg = bot.send_message(chat_id, "⌛", reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))
            text_conv = text_convert(chat_id,chatbot, UsersPromts[chat_id])
            bot_reply, plen = text_conv.main(message.text, 0, True)
            t = threading.Thread(target=send_image, args=(message.chat.id, message.text))
            t.start()
            if AllStages[int(chat_id)][-1] != 'TextReq': return


            all_text_to_image = ''
            if AllStages[int(chat_id)][-1] != 'TextReq': return
            if UsersOuts[message.chat.id] == 'Text':
                bot.delete_message(chat_id, mdel.message_id)
                bot.delete_message(chat_id, msg.message_id)

                for i in range(1, plen):
                    if AllStages[int(chat_id)][-1] != 'TextReq': return
                    bot.send_message(chat_id, bot_reply, reply_markup=button_back())
                    bot_reply, plen = text_conv.main('', i)
                bot.send_message(chat_id, bot_reply,
                                 reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))
            elif UsersOuts[message.chat.id] == 'Voice':
                all_text = bot_reply
                for i in range(1, plen):
                    if AllStages[int(chat_id)][-1] != 'TextReq': return
                    bot_reply, plen = text_conv.main('', i)
                    all_text += '\n' + bot_reply

                bot.send_audio(chat_id, textSpeach.get_speech(all_text),
                               reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")),
                                title='Ваше сообщение')
                bot.delete_message(chat_id, mdel.message_id)
                bot.delete_message(chat_id, msg.message_id)
            elif UsersOuts[message.chat.id] == 'File':
                all_text = bot_reply
                for i in range(1, plen):
                    if AllStages[int(chat_id)][-1] != 'TextReq': return
                    bot_reply, plen = text_conv.main('', i)
                    all_text += '\n' + bot_reply
                bot.delete_message(chat_id, mdel.message_id)
                bot.delete_message(chat_id, msg.message_id)
                bot.send_document(chat_id, text_to_pdf(all_text), visible_file_name='Ваше сообщение' + '.pdf', reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))
            # if t == None:
            if images[message.chat.id] == None:
                with open('p.gif', 'rb') as f:
                    m = bot.send_animation(chat_id, f)
                t.join()
                bot.edit_message_media(chat_id=message.chat.id, message_id=m.message_id,
                                       media=types.InputMediaPhoto(images[message.chat.id]))
            elif images[message.chat.id] != None:
                bot.send_photo(chat_id, images[message.chat.id])

            images[message.chat.id] = None


    elif AllStages[message.chat.id][-1] == 'Discus':
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][0] = 'Discus'
            AllStages[message.chat.id][-1] = 'StartMenu'
            start(message)
        else:
            bot.send_message(message.chat.id, chatbot.process_message_with_manual_cancel(message.chat.id,message.text), reply_markup=button_back())
    elif AllStages[message.chat.id][-1] == 'ExpParamT': #new
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][-1] = 'StartMenu'
            AllStages[message.chat.id][-1] = 'ExpParamT'
            start(message)
        else:
            UsersPromts[message.chat.id]=message.text
            AllStages[message.chat.id][-1] = 'Settings' #new
            AllStages[message.chat.id][0] = 'ExpParamT'
            btn0 = types.KeyboardButton("📝Параметры сжатия📝") #new
            btn1 = types.KeyboardButton("📤Тип вывода📤") #new
            bot.send_message(message.chat.id, 'Параметры сжатия успешно установлены!')
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?', reply_markup=button_back().add(btn0, btn1)) #new
    elif AllStages[message.chat.id][-1] == 'OutParamT':# new
        if message.text == '⬅Назад⬅':
            AllStages[message.chat.id][-1] = 'StartMenu'
            AllStages[message.chat.id][0] = 'OutParamT'
            start(message)
        elif message.text == "📝Текстом в сообщении📝":
            UsersOuts[message.chat.id] = 'Text'
            AllStages[message.chat.id][-1] = 'Settings' #new
            AllStages[message.chat.id][0] = 'OutParamT'
            btn0 = types.KeyboardButton("📝Параметры сжатия📝") #new
            btn1 = types.KeyboardButton("📤Тип вывода📤") #new
            bot.send_message(message.chat.id, 'Тип выводимого файла успешно установлен!')
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?', reply_markup=button_back().add(btn0, btn1)) #new
        elif message.text == '📁PDF файлом📁':
            UsersOuts[message.chat.id] = 'File'
            AllStages[message.chat.id][-1] = 'Settings' #new
            AllStages[message.chat.id][0] = 'OutParamT'
            btn0 = types.KeyboardButton("📝Параметры сжатия📝") #new
            btn1 = types.KeyboardButton("📤Тип вывода📤") #new
            bot.send_message(message.chat.id, 'Тип выводимого файла успешно установлен!')
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?', reply_markup=button_back().add(btn0, btn1)) #new
        elif message.text == '🔈Голосовым сообщением🔈':
            UsersOuts[message.chat.id] = 'Voice'
            AllStages[message.chat.id][-1] = 'Settings' #new
            AllStages[message.chat.id][0] = 'OutParamT'
            btn0 = types.KeyboardButton("📝Параметры сжатия📝") #new
            btn1 = types.KeyboardButton("📤Тип вывода📤") #new
            bot.send_message(message.chat.id, 'Тип выводимого файла успешно установлен!')
            bot.send_message(message.chat.id, 'Что бы вы хотели изменить?', reply_markup=button_back().add(btn0, btn1)) #new
        else:
            btn0 = types.KeyboardButton("📝Текстом в сообщении📝") #new
            btn1 = types.KeyboardButton("📁PDF файлом📁")
            btn2 = types.KeyboardButton("🔈Голосовым сообщением🔈")
            bot.send_message(message.chat.id, "Такого типа вывода у нас нет :(", reply_markup=button_back().add(btn0, btn1, btn2))

@bot.message_handler(content_types=['document'])
def get_file(message):
    global AllStages, images
    if AllStages[message.chat.id][-1] == 'FileReq':
        chat_id = message.chat.id
        directory = str(message.chat.id)
        if AllStages[int(chat_id)][-1] != 'FileReq': return
        if not os.path.exists(directory):
            os.mkdir(directory)
        if AllStages[int(chat_id)][-1] != 'FileReq': return
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name
        mdel = bot.send_message(message.chat.id, f"Файл {file_name} обрабатывается, ожидайте")
        msg = bot.send_message(chat_id, "⌛", reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))
        mime_type, _ = mimetypes.guess_type(file_name)
        if AllStages[int(chat_id)][-1] != 'FileReq': return
        if mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']:
            downloaded_file = bot.download_file(file_info.file_path)
            path = os.path.join(directory, file_name)
            with open(path, 'wb') as new_file:
                new_file.write(downloaded_file)
            text_conv=text_convert(message.chat.id,chatbot, UsersPromts[chat_id])
            bot_reply, plen = text_conv.main(path, 0)
            t = None
            all_text_to_image = ''
            if AllStages[int(chat_id)][-1] != 'FileReq': return
            if UsersOuts[message.chat.id] == 'Text':
                bot.delete_message(chat_id, mdel.message_id)
                bot.delete_message(chat_id, msg.message_id)

                for i in range(1, plen):
                    if AllStages[int(chat_id)][-1] != 'FileReq': return
                    bot.send_message(chat_id, bot_reply,reply_markup=button_back())
                    bot_reply, plen = text_conv.main('', i)
                bot.send_message(chat_id, bot_reply, reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")))
            elif UsersOuts[message.chat.id] == 'Voice':
                all_text = bot_reply
                for i in range(1, plen):
                    if AllStages[int(chat_id)][-1] != 'FileReq': return
                    bot_reply, plen = text_conv.main('', i)
                    all_text += '\n' + bot_reply

                bot.send_audio(chat_id, textSpeach.get_speech(all_text),
                               reply_markup=button_back().add(types.KeyboardButton("📖Задать вопрос по тексту📖")),
                               title=file_name)
                bot.delete_message(chat_id, mdel.message_id)
                bot.delete_message(chat_id, msg.message_id)
            elif UsersOuts[message.chat.id] == 'File':
                all_text = bot_reply
                for i in range(1, plen):
                    if AllStages[int(chat_id)][-1] != 'FileReq': return
                    bot_reply, plen = text_conv.main('', i)
                    all_text += '\n' + bot_reply
                bot.delete_message(chat_id, mdel.message_id)
                bot.delete_message(chat_id, msg.message_id)
                bot.send_document(chat_id, text_to_pdf(all_text), visible_file_name=file_name + '.pdf')
            #if t == None:
            '''t = threading.Thread(target=send_image, args=(message.chat.id, bot_reply, m))
            t.start()'''


        else:
            bot.send_message(message.chat.id, "Неподдерживаемый тип файла. Пожалуйста, загрузите файл в формате .docx или .txt.")





@bot.callback_query_handler(func=lambda call: True) #функция перехвата кнопок
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
        if AllStages[int(ChoiceSearch[3])][-1] != 'BookReq': return
        mdel = bot.send_message(chat_id, f"Книга {ChoiceSearch[0]} страница {ChoiceSearch[2]} обрабатывается, ожидайте")
        msg = bot.send_message(chat_id, "⌛", reply_markup=button_back())

        path_to_text = parsing.ParsingProductText(ChoiceSearch)
        with open(path_to_text, 'r', encoding='utf-8') as file:
            textBook = json.load(file)
            #print(textBook)
        txt = textBook['chapterText' + str(ChoiceSearch[2])]
        if AllStages[int(ChoiceSearch[3])][-1] != 'BookReq': return
        text_conv = text_convert(chat_id,chatbot, UsersPromts[chat_id])
        bot_reply, plen = text_conv.main(txt, 0, True)
        t = threading.Thread(target=send_image, args=(chat_id, txt))
        t.start()
        bot_reply = textBook['title'] + '\n' + textBook['chapterName' + str(ChoiceSearch[2])] + '\n\n' + bot_reply


        if AllStages[int(ChoiceSearch[3])][-1] != 'BookReq': return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if ChoiceSearch[2]==1:markup.row(types.KeyboardButton(f'Страница {ChoiceSearch[2]+1}')).row(types.KeyboardButton("📖Задать вопрос по тексту📖")).row(types.KeyboardButton("⬅Назад⬅"))
        elif ChoiceSearch[2]==textBook['count_all_pages']:markup.row(types.KeyboardButton(f'Страница {ChoiceSearch[2]-1}')).row(types.KeyboardButton("📖Задать вопрос по тексту📖")).row(types.KeyboardButton("⬅Назад⬅"))
        else:markup.row(types.KeyboardButton(f'Страница {ChoiceSearch[2]-1}'),types.KeyboardButton(f'Страница {ChoiceSearch[2]+1}')).row(types.KeyboardButton("📖Задать вопрос по тексту📖")).row(types.KeyboardButton("⬅Назад⬅"))


        all_text_to_image = ''
        if UsersOuts[chat_id] == 'Text':
            bot.delete_message(chat_id, mdel.message_id)
            bot.delete_message(chat_id, msg.message_id)

            for i in range(1, plen):
                if AllStages[int(chat_id)][-1] != 'BookReq': return
                bot.send_message(chat_id, bot_reply, reply_markup=button_back())
                bot_reply, plen = text_conv.main('', i)
            bot.send_message(chat_id, bot_reply, reply_markup=markup)
        elif UsersOuts[chat_id] == 'Voice':
            all_text = bot_reply
            for i in range(1, plen):
                if AllStages[int(chat_id)][-1] != 'BookReq': return
                bot_reply, plen = text_conv.main('', i)
                all_text += '\n' + bot_reply

            bot.send_audio(chat_id, textSpeach.get_speech(all_text),
                           reply_markup=markup,
                           title=textBook['title'] + '\n' + textBook['chapterName' + str(ChoiceSearch[2])])
            bot.delete_message(chat_id, mdel.message_id)
            bot.delete_message(chat_id, msg.message_id)
        elif UsersOuts[chat_id] == 'File':
            all_text = bot_reply
            for i in range(1, plen):
                if AllStages[int(chat_id)][-1] != 'BookReq': return
                bot_reply, plen = text_conv.main('', i)
                all_text += '\n' + bot_reply
            bot.delete_message(chat_id, mdel.message_id)
            bot.delete_message(chat_id, msg.message_id)
            bot.send_document(chat_id, text_to_pdf(all_text), visible_file_name=textBook['title'] + '\n' + textBook['chapterName' + str(ChoiceSearch[2])] + '.pdf',  reply_markup=markup)
        # if t == None:
        if images[chat_id] == None:
            with open('p.gif', 'rb') as f:
                m = bot.send_animation(chat_id, f)
            t.join()
            bot.edit_message_media(chat_id=chat_id, message_id=m.message_id,
                                   media=types.InputMediaPhoto(images[chat_id]))
        else:
            bot.send_photo(chat_id, images[chat_id])

        images[chat_id] = None


    except ZeroDivisionError:# Exception as e:
        #print(e)
        pass
'''def polling():
    
k = threading.Thread(target=polling)
k.start()
'''
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(5)