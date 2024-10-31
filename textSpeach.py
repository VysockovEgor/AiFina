import requests
import uuid


auth = 'ZmZlYmZhMDMtNzJkYS00MTgwLWE2NzQtZDI2ZWJhYWYyY2M5OjNmZTY3MDA1LWE0OTMtNGJmMi1iZmQwLWIyMDhiZDQzN2UxOQ=='

def get_token(auth_token, scope='SALUTE_SPEECH_PERS'):
    """
      Выполняет POST-запрос к эндпоинту, который выдает токен.

      Параметры:
      - auth_token (str): токен авторизации, необходимый для запроса.
      - область (str): область действия запроса API. По умолчанию — «SALUTE_SPEECH_PERS».

      Возвращает:
      - ответ API, где токен и срок его "годности".
      """
    # Создадим идентификатор UUID (36 знаков)
    rq_uid = str(uuid.uuid4())

    # API URL
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    # Заголовки
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'RqUID': rq_uid,
        'Authorization': f'Basic {auth_token}'
    }

    # Тело запроса
    payload = {
        'scope': scope
    }

    try:
        # Делаем POST запрос с отключенной SSL верификацией
        # (можно скачать сертификаты Минцифры, тогда отключать проверку не надо)
        response = requests.post(url, headers=headers, data=payload, verify=False)
        return response
    except requests.RequestException as e:
        print(f"Ошибка: {str(e)}")
        return None
    



def synthesize_speech(text, token, format='wav16', voice='Tur_24000'):
    url = "https://smartspeech.sber.ru/rest/v1/text:synthesize"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/text"
    }
    params = {
        "format": format,
        "voice": voice
    }
    response = requests.post(url, headers=headers, params=params, data=text.encode(), verify=False)

    if response.status_code == 200:
        return response.content
        # Сохранение синтезированного аудио в файл
        '''with open('output.wav', 'wb') as f:
            f.write(response.content)'''
        #print("Аудио успешно синтезировано и сохранено как 'output.wav'")
    else:
        return None


def get_speech(txt):
    response = get_token(auth)
    if response != None:
        salute_token = response.json()['access_token']
    return(synthesize_speech(txt, salute_token))
