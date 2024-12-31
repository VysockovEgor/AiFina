import faiss
import numpy as np
import json
import re
import ast
from sentence_transformers import SentenceTransformer
from OpenAI_Connected import generate

class BookRecommender:
    def __init__(self, model_name='all-MiniLM-L6-v2', vector_dim=384 * 3, faiss_index="db/book_index.faiss", map_file="db/book_map.json"):
        self.model = SentenceTransformer(model_name)
        self.vector_dim = vector_dim
        self.faiss_index = faiss_index
        self.map_file = map_file
        self.index = faiss.read_index(self.faiss_index)
        with open(self.map_file, "r") as f:
            self.book_map = {int(k): v for k, v in json.load(f).items()}

    def extract_between_braces(self, text):
        match = re.search(r'\{(.*?)\}', text, re.DOTALL)
        return match.group(1) if match else None

    def create_json(self, book_name):
        prompt = '''Создай JSON с описанием книги по трем критериям: жанр, тональность, темы. Пример:
        {
            "жанр": ["фэнтези", "эпос"],
            "тональность": ["величественная", "эпическая"],
            "темы": ["магия", "битвы", "древние легенды"]
        }'''

        response = generate(prompt, book_name)
        try:
            json_data = '{' + self.extract_between_braces(response) + '}'
            return ast.literal_eval(json_data)
        except Exception as e:
            print(f"Ошибка создания JSON: {e}")
            return None

    def vectorize_query(self, query_data):
        genre_text = " ".join(query_data['жанр'])
        tone_text = " ".join(query_data['тональность'])
        themes_text = " ".join(query_data['темы'])

        genre_vector = self.model.encode(genre_text)
        tone_vector = self.model.encode(tone_text)
        themes_vector = self.model.encode(themes_text)

        return np.concatenate([genre_vector, tone_vector, themes_vector]).astype(np.float32)

    def recommend_books(self, query_text, top_n=10):
        query_data = None
        for _ in range(5):
            query_data = self.create_json(query_text)
            if query_data:
                break
            print("Попытка создать JSON не удалась, повтор.")

        if not query_data:
            return None

        query_vector = self.vectorize_query(query_data)
        distances, indices = self.index.search(np.array([query_vector]), top_n)
        return [self.book_map[i] for i in indices[0] if i in self.book_map]




