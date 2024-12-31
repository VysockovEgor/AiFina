from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import re
from nltk.corpus import stopwords
import os
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.lib.enums import TA_JUSTIFY
from io import BytesIO
from reportlab.lib.fonts import addMapping

russian_stopwords = stopwords.words('russian')
db_name = "db/lsat_response.db"
if not os.path.exists(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS texts (
                id TEXT PRIMARY KEY,
                text TEXT
            )
        """)
    conn.commit()
    conn.close()

def text_to_pdf(text):
    pdf_stream = BytesIO()
    doc = SimpleDocTemplate(pdf_stream, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=20 * mm,
                            bottomMargin=20 * mm)

    pdfmetrics.registerFont(TTFont('Helvetica', 'Helvetica.ttf'))
    addMapping('Helvetica', 0, 0, 'Helvetica')

    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'Helvetica'
    styles['Normal'].fontSize = 12
    styles['Normal'].leading = 14
    styles['Normal'].alignment = TA_JUSTIFY

    story = []

    text_with_breaks = text.replace('\n', '<br/>')
    paragraph = Paragraph(text_with_breaks, styles['Normal'])
    story.append(paragraph)

    doc.build(story)
    pdf_stream.seek(0)
    return pdf_stream
def upsert_text(record_id: str, text: str):
    """Добавляет новую запись или обновляет текст, если запись с таким id уже существует."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO texts (id, text) VALUES (?, ?)
        ON CONFLICT(id) DO UPDATE SET text=excluded.text
    """, (record_id, text))
    conn.commit()
    conn.close()

def get_text_by_id(record_id: str) -> str:
    """Извлекает текст по указанному id. Возвращает None, если id не найден."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM texts WHERE id = ?", (record_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def split_text_with_langchain(text, max_tokens=512, overlap=0):
    """
    Разделение текста на чанки с использованием RecursiveCharacterTextSplitter.
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("Текст не должен быть пустым.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=overlap,  # Перекрытие между чанками для связности
        separators=["\n\n", "\n", ".", "?", "!", " "]
    )
    chunks = splitter.split_text(text)

    if not chunks:
        raise ValueError("Не удалось разделить текст на чанки.")

    # Дополнительная проверка на пустые чанки
    chunks = [chunk for chunk in chunks if chunk.strip()]
    '''for i in chunks:
        print(i)
        print('-'*50)'''

    if not chunks:
        raise ValueError("Все чанки пусты после разделения.")

    return chunks


def get_top_keywords(text, top_n=5):
    """
    Получение топ-ключевых слов с использованием TF-IDF.
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("Текст не должен быть пустым.")

    vectorizer = TfidfVectorizer(stop_words=russian_stopwords, max_features=top_n)
    tfidf_matrix = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray().flatten()

    # Получаем топ ключевых слов
    top_keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
    return [keyword for keyword, score in top_keywords]


def rank_chunks_by_tfidf_keywords(chunks, keywords):

    if not chunks or not keywords:
        raise ValueError("Чанки и ключевые слова не могут быть пустыми.")

    vectorizer = TfidfVectorizer(stop_words=russian_stopwords)

    chunk_vectors = vectorizer.fit_transform(chunks).toarray()

    keyword_vectors = vectorizer.transform([' '.join(keywords)]).toarray().flatten()

    ranked_chunks = []
    for chunk, chunk_vector in zip(chunks, chunk_vectors):
        similarity = sum(chunk_vector * keyword_vectors)
        ranked_chunks.append((chunk, similarity))

    ranked_chunks = sorted(ranked_chunks, key=lambda x: x[1], reverse=True)

    return ranked_chunks

def answer(id, sentence):
    text = get_text_by_id(id)
    chunks = re.split(r'(?<=[.!?]) +', text.strip())
    vectorizer = TfidfVectorizer(stop_words=russian_stopwords)
    chunk_vectors = vectorizer.fit_transform(chunks).toarray()
    keyword_vectors = vectorizer.transform([sentence]).toarray().flatten()

    ranked_chunks = []
    for chunk, chunk_vector in zip(chunks, chunk_vectors):
        similarity = sum(chunk_vector * keyword_vectors)
        ranked_chunks.append((chunk, similarity))

    ranked_chunks = sorted(ranked_chunks, key=lambda x: x[1], reverse=True)

    return ' '.join([ranked_chunks[i][0].replace('\n','').replace('\t','') for i in range(min(5, len(ranked_chunks)))])


def extractive_summary(text, sentences_count=5):
    """
    Экстрактивная суммаризация текста с использованием TextRank.
    """
    if not text or len(text.strip()) == 0:
        raise ValueError("Текст не должен быть пустым.")

    parser = PlaintextParser.from_string(text, Tokenizer("russian"))
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join(str(sentence) for sentence in summary)


def summarize_large_text(id):
    """
    Суммаризация большого текста с использованием экстрактивного подхода,
    токенизации и обработки чанков.
    """
    text = get_text_by_id(id)
    # 1. Экстрактивная суммаризация
    short_text = extractive_summary(text, sentences_count=10)
    #print(f"Экстрактивная суммаризация:\n{short_text}")

    # 2. Получаем топ-ключевые слова
    keywords = get_top_keywords(short_text, top_n=5)
    #print(f"Ключевые слова: {keywords}")

    # 3. Разделение на чанки с помощью LangChain
    chunks = split_text_with_langchain(short_text, max_tokens=1024)
    #print(f"Чанки: {chunks}")

    # 4. Ранжирование чанков по ключевым словам
    ranked_chunks = rank_chunks_by_tfidf_keywords(chunks, keywords)
    #print(f"Ранжированные чанки: {ranked_chunks}")

    # 5. Создание итогового текста
    final_summary = [chunk for chunk, _ in ranked_chunks]

    return chunks



