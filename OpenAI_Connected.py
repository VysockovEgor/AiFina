'''import asyncio
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.gERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
langfuse 2.51.5 requires httpx<1.0,>=0.15.4, but you have httpx 0.13.3 which is incompatible.
langfuse 2.51.5 requires idna<4.0,>=3.7, but you have idna 2.10 which is incompatible.
langsmith 0.1.132 requires httpx<1,>=0.23.0, but you have httpx 0.13.3 which is incompatible.
Successfully installed chardet-3.0.4 googletrans-4.0.0rc1 h11-0.9.0 httpcore-0.9.1 httpx-0.13.3 idna-2.10
rpc.api.status import status_code_pb2
from functools import partial

async def generate_image_bytes(prompt: str) -> bytes:
    # Настройки пользователя и модели
    PAT = '810adbb875024c5e9b0046761e5b7aba'
    USER_ID = 'stability-ai'
    APP_ID = 'stable-diffusion-2'
    MODEL_ID = 'stable-diffusion-xl'
    MODEL_VERSION_ID = '68eeab068a5e4488a685fc67bc7ba71e'

    # Создание канала и stub
    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)
    metadata = (('authorization', 'Key ' + PAT),)

    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

    # Подготовка запроса
    request = service_pb2.PostModelOutputsRequest(
        user_app_id=userDataObject,
        model_id=MODEL_ID,
        version_id=MODEL_VERSION_ID,
        inputs=[
            resources_pb2.Input(
                data=resources_pb2.Data(
                    text=resources_pb2.Text(raw=prompt)
                )
            )
        ]
    )

    # Запуск синхронного запроса в отдельном потоке
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, partial(stub.PostModelOutputs, request, metadata=metadata))

    # Проверка успешности запроса
    if response.status.code != status_code_pb2.SUCCESS:
        raise Exception(f"Post model outputs failed, status: {response.status.description}")

    # Возврат байтов изображения
    return response.outputs[0].data.image.base64

# Пример вызова функции
async def main():
    image_bytes = await generate_image_bytes("funny parrot")
    with open("output.jpg", "wb") as f:
        f.write(image_bytes)

# Запуск асинхронного кода
asyncio.run(main())
'''
from math import gamma

'''from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat

llm = GigaChat(
        credentials="NmM2NGJlM2EtZTAxNi00ZDNkLTgwODMtYTMwYTQwYmE5NmQ0OmZiZDc0NjYyLTZlM2EtNDAxNC04MzY4LTU2N2M3OWJlODg1OA==",
        scope="GIGACHAT_API_PERS",
        model="GigaChat",
        verify_ssl_certs=False,
        #max_tokens=100
        )
prompt = llm.invoke([
             HumanMessage(content="Привет")
    ]).content
print(prompt)'''



from openai import OpenAI
import httpx
import requests
from keys import OPENAI_API_KEY, PROXY_SERVER_URL


client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx.Client(proxy=PROXY_SERVER_URL))
async def generate_image(text: str) -> bytes:
    prompt = generate(
        "Create an illustration inspired by the text. Visualize the central themes, atmosphere, and tone of the text using an appropriate color palette, style, and composition. If the text does not contain specific objects or characters, focus on abstract elements, symbols, or metaphors that convey the essence and emotions of the text. Avoid detailed depictions of faces; instead, focus on the context and aesthetics. Ensure that the mood, tone, and essence of the narrative are represented through visual cues. Write prompt in English!",
        text)
    response = client.images.generate(
      model="dall-e-3",
      prompt=prompt,
      size="1024x1024",
      quality="standard",
      n=1,
    )
    response = (requests.get(response.data[0].url).content)
    print("Image was generated", type(response))
    return response

def generate(system_prompt,human_prompt=None):
    res = [
            {"role": "system", "content": system_prompt},

        ]
    if human_prompt: res.append({
                "role": "user",
                "content": human_prompt
            })
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=res
    )
    return completion.choices[0].message.content
