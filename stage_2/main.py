import os
import tempfile
import streamlit as st
import asyncio
from langchain_community.llms import LlamaCpp
from llama_index.core import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

class TextSummarizerApp:
    """
    Приложение для сокращения текста и документов, поддерживающее выбор уровня сокращения и стиля текста.
    """

    def __init__(self):
        # Заданные размеры для экстрактивного суммаризатора и стили сокращений
        self.ex_size = {"Сильная": 1, "Слабая": 5}
        self.prompts = {
            "Сильная": {
                "Креативный": "Будь креативным и сократи текст до одного предложения.\n\n{text}\n\nСУММАРИЗАЦИЯ:",
                "Обычный": "Сократи текст до одного предложения.\n\n{text}\n\nКРАТКАЯ СУММАРИЗАЦИЯ:",
                "Академический": "Суммируй текст в одном академическом предложении.\n\n{text}\n\nАКАДЕМИЧЕСКАЯ СУММАРИЗАЦИЯ:"
            },
            "Слабая": {
                "Креативный": "Будь креативным, дай краткое резюме текста ниже.\n\n{text}\n\nСУММАРИЗАЦИЯ:",
                "Обычный": "Напиши краткое резюме текста.\n\n{text}\n\nКРАТКАЯ СУММАРИЗАЦИЯ:",
                "Академический": "Суммируй текст в академическом стиле.\n\n{text}\n\nАКАДЕМИЧЕСКАЯ СУММАРИЗАЦИЯ:"
            }
        }

        # Инициализация токенизатора и алгоритма TextRank для экстрактивного суммаризатора
        self.tokenizer = Tokenizer("russian")
        self.summarizer = TextRankSummarizer()

        # Настройки модели LlamaCpp
        self.llm = LlamaCpp(
            model_path="C:/Users/user/.cache/lm-studio/models/TheBloke/Llama-2-13B-chat-GGUF/llama-2-13b-chat.Q3_K_S.gguf",
            temperature=0.5,
            n_gpu_layers=-1,
            n_batch=512,
            n_ctx=512,
            max_tokens=100,
            top_p=0.9,
            verbose=True
        )

        # Разделитель текста для подготавки чанков текста
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=256,
            chunk_overlap=20,
            separators=["\n", "\n\n", " ", ""]
        )

    async def extractive_summary(self, text, num_sentences):
        """
        Выполняет экстрактивное сокращение текста с использованием TextRank.

        :param text: исходный текст
        :param num_sentences: количество предложений в сокращенной версии
        :return: строка с экстрактивным сокращением
        """
        parser = PlaintextParser.from_string(text, self.tokenizer)
        summary = self.summarizer(parser.document, num_sentences)
        return ' '.join(str(sentence) for sentence in summary)

    async def summarize_chunk(self, chunk):
        """
        Суммаризирует один текстовый фрагмент с использованием LLMChain.

        :param chunk: фрагмент текста для суммаризации
        :return: суммаризированный текст
        """
        response = await asyncio.to_thread(self.llm_chain.invoke, {"text": chunk})
        return response

    async def summarize_text(self, text, summarization_level, writing_style):
        """
        Суммаризирует текст, используя заданный уровень сокращения и стиль.

        :param text: текст для сокращения
        :param summarization_level: уровень сокращения ("Сильная" или "Слабая")
        :param writing_style: стиль ("Креативный", "Обычный" или "Академический")
        """
        # Создание шаблона для генерации на основе выбранного уровня и стиля
        prompt_template = PromptTemplate(
            input_variables=["text"],
            template=self.prompts[summarization_level][writing_style] + " Сократи текст без комментариев: {text}"
        )
        self.llm_chain = prompt_template | self.llm

        # Получение экстрактивного сокращения и разделение на чанки
        ex_sum = await self.extractive_summary(text, num_sentences=self.ex_size[summarization_level])
        merged_chunks = self.text_splitter.split_text(ex_sum)

        # Список для хранения промежуточных результатов суммаризаций
        summaries = [None] * len(merged_chunks)
        tasks = [(self.summarize_chunk(chunk), i) for i, chunk in enumerate(merged_chunks)]

        response_container = st.empty()

        # Обновление результата для каждого чанка, как только они готовы
        for task, index in tasks:
            summary = await task
            if summary:
                summaries[index] = summary
                response_container.empty()
                response_container.write("\n\n".join(s for s in summaries if s is not None))

    async def summarize_documents(self, files, summarization_level, writing_style):
        """
        Выполняет суммаризацию загруженных файлов.

        :param files: список загруженных файлов
        :param summarization_level: уровень сокращения
        :param writing_style: стиль текста
        """
        for file in files:
            file_content = self.extract_text_from_file(file)
            text = Document(text=file_content).text
            st.header(f"Суммаризация для файла: {file.name}")
            await self.summarize_text(text, summarization_level, writing_style)

    def extract_text_from_file(self, uploaded_file):
        """
        Извлекает текст из загруженного файла в зависимости от его типа.

        :param uploaded_file: файл, загруженный пользователем
        :return: текст, извлеченный из файла
        """
        file_extension = uploaded_file.name.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        # Определение загрузчика в зависимости от формата файла
        if file_extension == "pdf":
            loader = PyPDFLoader(temp_file_path)
        elif file_extension in ["docx", "doc"]:
            loader = Docx2txtLoader(temp_file_path)
        elif file_extension == "txt":
            loader = TextLoader(temp_file_path)
        else:
            raise ValueError(f"Формат файла {file_extension} не поддерживается.")

        documents = loader.load()
        os.remove(temp_file_path)
        return "\n".join(doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in documents)

    def show_menu(self):
        """
        Отображает боковое меню для выбора страницы.

        :return: выбранная пользователем страница
        """
        st.sidebar.title("Меню")
        return st.sidebar.selectbox("Выберите страницу", ["Сокращение текста", "Сокращение документов"])

    def show_summarization_options(self):
        """
        Отображает настройки для выбора уровня сокращения и стиля текста.

        :return: выбранный уровень сокращения и стиль текста
        """
        summarization_level = st.selectbox("Выберите степень сокращения", ["Сильная", "Слабая"])
        writing_style = st.selectbox("Выберите стиль текста", ["Креативный", "Обычный", "Академический"])
        return summarization_level, writing_style

    def run(self):
        """
        Запускает приложение Streamlit и управляет его основными функциями.
        """
        st.markdown('<h1 style="color: #134E19;">Сокращение текста и документов от AiFina</h1>', unsafe_allow_html=True)
        page = self.show_menu()

        if page == "Сокращение текста":
            text = st.text_area("Введите текст", "")
            summarization_level, writing_style = self.show_summarization_options()

            if st.button("Сократить текст", key="shorten_text_button"):
                if text:
                    asyncio.run(self.summarize_text(text, summarization_level, writing_style))
                    st.success("Сокращение текста завершено!")
                else:
                    st.error("Введите текст для сокращения.")

        elif page == "Сокращение документов":
            uploaded_files = st.file_uploader("Загрузите документы", accept_multiple_files=True, type=["pdf", "docx", "txt"])
            summarization_level, writing_style = self.show_summarization_options()

            if st.button("Сократить документы", key="shorten_documents_button"):
                if uploaded_files:
                    asyncio.run(self.summarize_documents(uploaded_files, summarization_level, writing_style))
                    st.success("Сокращение документов завершено!")
                else:
                    st.error("Загрузите хотя бы один документ.")

# Запуск приложения
if __name__ == "__main__":
    app = TextSummarizerApp()
    app.run()
