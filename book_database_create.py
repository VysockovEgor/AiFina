import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer

# Инициализация модели Sentence-BERT
model = SentenceTransformer('all-MiniLM-L6-v2')

# Определение размерности векторов
VECTOR_DIM = 384 * 3


class BookDatabase:
    def __init__(self):
        self.index = faiss.IndexFlatL2(VECTOR_DIM)  # Создаем индекс для поиска по L2-норме
        self.book_map = {}  # Хранилище соответствия индексов FAISS и названий книг

    def json_to_vector(self, data):
        genre_text = " ".join(data['жанр'])
        tone_text = " ".join(data['тональность'])
        themes_text = " ".join(data['темы'])

        genre_vector = model.encode(genre_text)
        tone_vector = model.encode(tone_text)
        themes_vector = model.encode(themes_text)

        combined_vector = np.concatenate([genre_vector, tone_vector, themes_vector])
        return combined_vector

    def add_book(self, book_name, book_data):
        vector = self.json_to_vector(book_data)

        self.index.add(np.array([vector], dtype=np.float32))
        self.book_map[len(self.book_map)] = book_name

    def find_similar_books(self, query_vector, top_n=10):
        query_vector = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(query_vector, top_n)
        print(f"Дистанции: {distances}, Индексы: {indices}")

        # Фильтруем индексы и сопоставляем с названиями книг
        similar_books = [self.book_map[i] for i in indices[0] if i in self.book_map]
        return similar_books[:top_n]

    def save_index(self, index_filename="book_index.faiss", map_filename="book_map.json"):
        faiss.write_index(self.index, index_filename)
        with open(map_filename, "w") as f:
            # Преобразуем ключи к строковому формату для совместимости с JSON
            json.dump({str(k): v for k, v in self.book_map.items()}, f)

    def load_index(self, index_filename="book_index.faiss", map_filename="book_map.json"):
        self.index = faiss.read_index(index_filename)
        with open(map_filename, "r") as f:
            # Преобразуем ключи обратно в целые числа
            self.book_map = {int(k): v for k, v in json.load(f).items()}


# Пример использования
db = BookDatabase()

books = [
    {
        "book_name": "Ужасы любви",
        "book_data": {
            "жанр": ["ужасы", "мелодрама"],
            "тональность": ["напряженная"],
            "темы": ["призраки", "страх", "психологическое давление"]
        }
    },
    {
        "book_name": "Космические приключения",
        "book_data": {
            "жанр": ["фантастика", "приключения"],
            "тональность": ["динамичная", "вдохновляющая"],
            "темы": ["космос", "исследования", "героизм"]
        }
    },
    {
        "book_name": "Загадки преступления",
        "book_data": {
            "жанр": ["детектив", "триллер"],
            "тональность": ["напряженная", "мрачная"],
            "темы": ["расследование", "загадки", "криминал"]
        }
    },
    {
        "book_name": "Легенды магии",
        "book_data": {
            "жанр": ["фэнтези", "эпос"],
            "тональность": ["величественная", "эпическая"],
            "темы": ["магия", "битвы", "древние легенды"]
        }
    },
    {
        "book_name": "Драматическая любовь",
        "book_data": {
            "жанр": ["романтика", "драма"],
            "тональность": ["эмоциональная", "трогательная"],
            "темы": ["любовь", "потери", "жизненные трудности"]
        }

    },
    {
        "book_name": "Мы",
        "book_data": {
            "жанр": ["фэнтези", "антиутопия"],
            "тональность": ["величественная", "эпическая"],
            "темы": ["социализм", "битвы", "древние легенды"]
        },

    }

]



def search_books(query_data):
    db = BookDatabase()
    db.load_index()

    query_vector = db.json_to_vector(query_data)
    print(f"Вектор запроса размерности: {query_vector.shape}")

    similar_books = db.find_similar_books(query_vector)
    return similar_books


# Пример запроса
query = {
    "жанр": ["роман"],
    "тональность": ["романтическая"],
    "темы": ["любовь"]
}

import re
import parsing
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
import ast
llm = GigaChat(
        credentials="NmM2NGJlM2EtZTAxNi00ZDNkLTgwODMtYTMwYTQwYmE5NmQ0OmYzOWNlOTc3LWM0ZTktNGY5Yi04ZTg4LTM4MWViNjBmZGZhMg==",
        scope="GIGACHAT_API_PERS",
        model="GigaChat",
        verify_ssl_certs=False,
        #max_tokens=100
        )
def extract_between_braces(text):
    match = re.search(r'\{(.*?)\}', text, re.DOTALL)  # Ищем текст между фигурными скобками
    if match:
        return match.group(1)  # Возвращаем только содержимое между скобками
    return None  # Если ск
def extract_book_title(text):
    # Используем регулярное выражение, чтобы извлечь текст между кавычками
    match = re.match(r'^\d+\.\s*"([^"]+)"\s*—', text)
    if match:
        return match.group(1).strip()  # Возвращаем название книги без кавычек и лишних пробелов
    return None  # Если совпадение не найдено, возвращаем None
ok = 0
# Пример использования
n=0
m = [extract_book_title(i) for i in open('books.txt', 'r')]
books_urls = []
b = open('books1.txt', 'w')

def create_json(name):
    res = llm.invoke([
        SystemMessage(content='''создай json описывающий книгу по трем критериям 1 жанр 2 тональность 3 темы. Для каждого критерия должен быть массив значений {
            "жанр": ["фэнтези", "эпос"],
            "тональность": ["величественная", "эпическая"],
            "темы": ["магия", "битвы", "древние легенды"]
        }'''),
        HumanMessage(content=name)
    ]).content
    json = '{'+extract_between_braces(res)+'}'
    magic = ast.literal_eval(json)
    return magic

for i in open('books_urls.txt', 'r'):
    try:
        name = i.replace('\n','').split(';)')[0]
        url = i.replace('\n','').split(';)')[1]
        magic = None
        for j in range(3):
            try:
                magic = create_json(name)
                break
            except Exception as e: print(e)
        if magic is not None:
            ok += 1
            print(ok, name, url)
            db.add_book(name+';)'+url, magic)
    except: pass

print(ok)
db.save_index()



