import os
import asyncio
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from langchain_community.chat_models.gigachat import GigaChat
from langchain_core.messages import HumanMessage, AIMessage

Base = declarative_base()
try:os.remove('chat_history.db')
except:print('NO DB')
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    message = Column(Text)
    sender = Column(String)

engine = create_engine("sqlite:///chat_history.db")
SessionLocal = sessionmaker(bind=engine)  
Base.metadata.create_all(engine)

class Chatbot:
    def __init__(self):
        self.model = GigaChat(
            credentials="NmM2NGJlM2EtZTAxNi00ZDNkLTgwODMtYTMwYTQwYmE5NmQ0OmYzOWNlOTc3LWM0ZTktNGY5Yi04ZTg4LTM4MWViNjBmZGZhMg==",
            scope="GIGACHAT_API_PERS",
            model="GigaChat",
            verify_ssl_certs=False,
            max_tokens=100
        )
        self.active_tasks = {}

    def add_message_to_db(self, user_id, message, sender):

        session = SessionLocal()  
        new_message = Message(user_id=user_id, message=message, sender=sender)
        session.add(new_message)
        session.commit()
        session.close()

    def get_user_history(self, user_id):
        session = SessionLocal()
        messages = session.query(Message).filter_by(user_id=user_id).all()
        session.close()

        history = []
        for msg in messages:
            if msg.sender == 'human':
                history.append(HumanMessage(content=msg.message))
            elif msg.sender == 'ai':
                history.append(AIMessage(content=msg.message))
        return history

    async def process_message(self, user_id, user_input):
        self.add_message_to_db(user_id, user_input, 'human')
        user_history = self.get_user_history(user_id)
        response = await asyncio.to_thread(self.model.invoke, user_history)
        ai_response = response.content
        self.add_message_to_db(user_id, ai_response, 'ai')
        return ai_response

    def process_message_with_manual_cancel(self, user_id, user_input):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(self.process_message(user_id, user_input))
        self.active_tasks[user_id] = task

        try:

            response = loop.run_until_complete(task)
            return response
        except asyncio.CancelledError:
            return f"Запрос был прерван."
        finally:
            loop.close()

    def cancel_user_message(self, user_id):
        task = self.active_tasks.get(user_id)
        if task and not task.done():
            task.cancel()
            return f"Задача для пользователя {user_id} отменена."
        return f"Задача для пользователя {user_id} не найдена или уже завершена."
    
'''chatbot = Chatbot()
print(chatbot.process_message_with_manual_cancel(1,'Hello'))'''