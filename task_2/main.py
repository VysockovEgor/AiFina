import os
import tempfile
import streamlit as st
from langchain_community.llms import LlamaCpp
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from llama_index.core import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage

class TextSummarizerApp:
    def __init__(self):
        self.chunk_size_labels = {"Сильная": 512, "Слабая": 50}
        self.prompts = {
            "Сильная": {
                "Креативный": "Будь креативным и сократи текст ниже до одного предложения.\n\n{text}\n\nСУММАРИЗАЦИЯ:",
                "Обычный": "Сократи текст ниже до одного предложения.\n\n{text}\n\nКРАТКАЯ СУММАРИЗАЦИЯ:",
                "Академический": "Суммируй следующий текст в одном академическом предложении.\n\n{text}\n\nАКАДЕМИЧЕСКАЯ СУММАРИЗАЦИЯ:"
            },
            "Слабая": {
                "Креативный": "Будь креативным и дай краткое резюме текста ниже.\n\n{text}\n\nСУММАРИЗАЦИЯ:",
                "Обычный": "Напиши краткое резюме текста ниже.\n\n{text}\n\nКРАТКАЯ СУММАРИЗАЦИЯ:",
                "Академический": "Суммируй следующий текст в академическом стиле.\n\n{text}\n\nАКАДЕМИЧЕСКАЯ СУММАРИЗАЦИЯ:"
            }
        }

        # Конфигурация модели LlamaCpp
        self.llm = LlamaCpp(
            model_path="C:/Users/user/.cache/lm-studio/models/hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF/llama-3.2-1b-instruct-q8_0.gguf",
            temperature=0.6,
            n_gpu_layers=-1,
            n_batch=512,
            n_ctx=512,
            max_tokens=1512,
            top_p=1,
            verbose=True
        )


    # Функция для объединения меньших чанков в родительские с проверкой уникальности
    def merge_chunks(self, chunks, threshold=200):
        merged_chunks = []
        current_chunk = ""

        for chunk in chunks:
            # Если длина текущего блока вместе с новым параграфом не превышает порог
            if len(current_chunk) + len(chunk) < threshold:
                current_chunk += chunk
            else:
                # Добавляем непустой текущий блок в результат и обнуляем для следующего параграфа
                if current_chunk:
                    merged_chunks.append(current_chunk)
                current_chunk = chunk

        # Добавляем последний непустой блок в результат
        if current_chunk:
            merged_chunks.append(current_chunk)

        return merged_chunks

    # Функция суммаризации текста с автослиянием чанков
    def summarize_text(self, text, summarization_level, writing_style):
        prompt_template = self.prompts[summarization_level][
                              writing_style]

        # Используем ChatPromptTemplate для создания более гибкого шаблона
        chat_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("Ты русская текстовая модель для литераторов. Сократи следующий текст и сделай смысловой переход от прошлого текста к нынешнему"),
            HumanMessagePromptTemplate.from_template(
                "Прошлый текст: {last_text}\nТекущий текст: {text}\n\n" + prompt_template)
        ])

        llm_chain = LLMChain(prompt=chat_prompt, llm=self.llm)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size_labels[summarization_level],
                                                       chunk_overlap=0)
        chunks = text_splitter.split_text(text)
        merged_chunks = self.merge_chunks(chunks)

        summaries = []
        last_summary = None
        for chunk in merged_chunks:
            chunk = chunk[:self.llm.max_tokens] if len(chunk) > self.llm.max_tokens else chunk
            summary = llm_chain.invoke({"last_text": last_summary or '', "text": chunk})['text']

            if summary not in summaries:
                summaries.append(summary)
                last_summary = summary
                st.write(summary)





    # Функция для суммаризации документов
    def summarize_documents(self, files, summarization_level, writing_style):
        full_summary = ""
        for file in files:
            file_content = self.extract_text_from_file(file)
            text = Document(text=file_content).text

            summaries = self.summarize_text(text, summarization_level, writing_style)
            full_summary += summaries + "\n\n"
        return full_summary

    # Извлечение текста из файла в зависимости от его формата
    def extract_text_from_file(self, uploaded_file):
        file_extension = uploaded_file.name.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        loader = None
        if file_extension == "pdf":
            loader = PyPDFLoader(temp_file_path)
        elif file_extension in ["docx", "doc"]:
            loader = Docx2txtLoader(temp_file_path)
        elif file_extension == "txt":
            loader = TextLoader(temp_file_path)
        else:
            raise ValueError(f"Формат файла {file_extension} не поддерживается.")

        documents = loader.load()
        os.remove(temp_file_path)  # Удаляем временный файл после загрузки текста
        text = "\n".join(doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in documents)
        return text

    # Отображение меню и обработка выбора страницы
    def show_menu(self):
        st.sidebar.title("Меню")
        page = st.sidebar.selectbox("Выберите страницу", ["Сокращение текста", "Сокращение документов"])
        return page

    # Настройки для выбора стиля и уровня суммаризации
    def show_summarization_options(self):
        summarization_level = st.selectbox("Выберите степень сокращения", ["Сильная", "Слабая"])
        writing_style = st.selectbox("Выберите стиль текста", ["Креативный", "Обычный", "Академический"])
        return summarization_level, writing_style

    # Запуск основной логики приложения
    def run(self):
        st.title("Сокращение текста и документов от AiFina")
        page = self.show_menu()

        if page == "Сокращение текста":
            text = st.text_area("Введите текст", "")
            summarization_level, writing_style = self.show_summarization_options()

            # Добавляем уникальные ключи к кнопкам
            if st.button("Сократить текст", key="shorten_text_button"):
                if text:
                    self.summarize_text(text, summarization_level, writing_style)
                    st.success("Сокращение текста завершено!")
                else:
                    st.error("Введите текст для сокращения.")

        elif page == "Сокращение документов":
            uploaded_files = st.file_uploader("Загрузите документы", accept_multiple_files=True,
                                              type=["pdf", "docx", "txt"])
            summarization_level, writing_style = self.show_summarization_options()

            # Добавляем уникальные ключи к кнопкам
            if st.button("Сократить документы", key="shorten_documents_button"):
                if uploaded_files:
                    self.summarize_documents(uploaded_files, summarization_level, writing_style)
                    st.success("Сокращение документов завершено!")
                else:
                    st.error("Загрузите хотя бы один документ.")


# Запуск приложения
if __name__ == "__main__":
    app = TextSummarizerApp()
    app.run()
