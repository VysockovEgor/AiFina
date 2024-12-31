
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from typing import AsyncGenerator, Dict, Union
from  extractive_summarization import *
import magic
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document
import pars
import base64
import json
import asyncio
from pydantic import BaseModel
from typing import List
from random import randint as r
from  OpenAI_Connected import *


from liderbord import get_sorted_users


# Подключение шаблонов
templates = Jinja2Templates(directory="templates")

app = FastAPI()
UsersPromts = {'5389593084':''}

async def extract_text_from_bytes(file_bytes):
    """
    Извлекает текст из документа, автоматически определяя его формат на основе содержимого.

    :param file_bytes: содержимое файла в байтах
    :return: извлеченный текст
    """
    file_bytes = await file_bytes.read()
    mime_type = magic.Magic(mime=True).from_buffer(file_bytes)
    if mime_type == "application/pdf":
        # Чтение PDF-файла из байтов
        pdf_reader = PdfReader(BytesIO(file_bytes))
        raw_text = "\n".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
    elif mime_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        # Чтение DOCX-файла из байтов
        doc = Document(BytesIO(file_bytes))
        raw_text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    elif mime_type.startswith("text/"):
        # Обработка текстового файла
        raw_text = file_bytes.decode("utf-8", errors="ignore")
    else:
        return "Неподдерживаемый формат файла! Пожалуйста, загрузите файл формата pdf, docx, doc или txt."
    return raw_text



# Функция для создания изображения (эмуляция)


n = 0
async def generate_data(text: str, id:str) -> AsyncGenerator[Dict[str, Union[str, bytes]], None]:
    global n
    n+=1
    upsert_text( id, text)
    text_chunks = summarize_large_text(id)
    transition_words = ["Далее", "Затем", "После этого", "Позже", "Впоследствии", "Тем временем", "С другой стороны",
                        "Между тем"]
    image_task = None
    k = len(text_chunks)
    first_message = ""
    for i in range(k):
        promts = [
            f"Создай компактное и информативное резюме текста, уложившись в одно предложение, при этом сохрани ключевые идеи и основной смысл, чтобы итоговый тезис был чётким и точным{first_message} Напиши все в пару слов!" + UsersPromts[id],
            text_chunks[i]
        ]
        if i:
            first_message = f' Начни со слов {transition_words[r(0, len(transition_words) - 1)]}'



        res = generate(promts[0], promts[1])
        '''print('=' * 50)
        print(text_chunks[i])
        print('-' * 50)
        print(res)
        print('=' * 50)'''
        if image_task is None:
            image_task = asyncio.create_task(generate_image(res))

        # Проверяем готовность изображения
        data = {'summary': res, 'image': None, "last":True if i==k-1 else False}
        yield json.dumps(data) + "\n"

    # Дожидаемся окончания генерации изображения
    image_bytes = await image_task
    '''with open('1.jpg', 'rb') as f:
        image_base64 = f.read()'''
    data = {'summary': None, 'image': base64.b64encode(image_bytes).decode('utf-8')}

    yield json.dumps(data) + "\n"

@app.get("/", response_class=HTMLResponse)
async def get_sorted_data(request: Request):
    users = get_sorted_users()  # Получаем отсортированных пользователей
    return templates.TemplateResponse("index.html", {"request": request, "users": users})

# Эндпоинт для получения и сохранения истории чата
@app.post("/text/")
async def simple_text(message: Dict[str, str]):
    print(1,message['id'])
    return StreamingResponse(generate_data(message["text"], message['id']), media_type="application/json")


@app.post("/file/")
async def upload_file(file: UploadFile = File(...), id: str = Form(...)):
    try:
        text = await extract_text_from_bytes(file)
        if text != "Неподдерживаемый формат файла! Пожалуйста, загрузите файл формата pdf, docx, doc или txt.":
            return StreamingResponse(generate_data(text, id), media_type="application/json")
        else:
            return {"error": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке файла: {e}")


@app.post("/find_book/")
async def find_book(message: Dict[str, str]):
    try:
        book_name = message["book_name"]
        books = pars.SearchProduct(book_name)
        return {"books": books}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска книги: {e}")


@app.post("/book/")
async def get_book(message: Dict[str, str]):
    try:
        url, page = message["url"].split('/'), message["page"]
        url[5] = url[5].split('.')
        url[5][1] = str(page)
        url[5] = '.'.join(url[5])
        url = '/'.join(url)
        page_content = pars.get_page(url)
        return StreamingResponse(generate_data(page_content, message['id']), media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения страницы книги: {e}")

class SettingsModel(BaseModel):
    promt: List[str]
@app.post("/settings/")
async def settings(message: SettingsModel):
    global UsersPromts
    if message.promt:  # Проверка на наличие данных
        UsersPromts[message.promt[0]] = message.promt[1]
        print(UsersPromts)

@app.post("/answer/")
async def answer_send(message: Dict[str, str]):
    sentences = answer(message['id'], message['question'])
    sentences = split_text_with_langchain(sentences, max_tokens=512, overlap=0)[0]
    print('='*50)
    print(sentences)
    print('-'*50)
    res = generate(sentences, message['question']+"Напиши ответ в 1 предложение!")
    print(res)
    return {'a':res}

@app.post("/test/")
async def test(message: Dict[str, str]):
    try:
        text = get_text_by_id(message['id'])
        text = extractive_summary(text, sentences_count=5)
        keywords = get_top_keywords(text, top_n=10)
        sentences1 = re.split(r'(?<=[.!?]) +', text.strip())
        ranked_chunks = rank_chunks_by_tfidf_keywords(sentences1, keywords)
        sentences2 = ' '.join([chunk for chunk, _ in ranked_chunks])
        sentences = split_text_with_langchain(sentences2, max_tokens=512, overlap=0)[0]
        res = generate('Сгенерируй 5 вопросов по тексту',sentences)
        print(res, type(res))
        return {"questions_and_answers": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки: {e}")



@app.get('/1/')
async def page():
    return 'Привет'

#uvicorn main:app --reload

'''import uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)'''