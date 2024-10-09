import requests
import json
import time
import base64

import re

#model = Summarizer()



class Text2ImageAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }
        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        response.raise_for_status()
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)
        return None

    def gen(self, text, dirr="images"):
        text = text.replace("\n", " ")
        #summary = model(text, num_sentences=1)
        summary=text
        prompt = re.sub(r'[^\w\s]', '', re.sub(r'\b\d{4} года\b', '', re.sub(r'\b\d{1,2} \w+ \d{4} года\b', '', summary)))
        #print('k:',prompt)
        prompt+=' Иллюстрация для сказок'
        model_id = self.get_model()
        uuid = self.generate(prompt, model_id)
        images = self.check_generation(uuid)

        if images and len(images) > 0:
            image_base64 = images[0]

            image_data = base64.b64decode(image_base64)
            return image_data
            '''
            filename = os.path.join(dirr, "1.jpg")  # Save the image in the specified directory
            with open(filename, "wb") as file:
                file.write(image_data)'''


'''api = Text2ImageAPI('https://api-key.fusionbrain.ai/', 'FFF38A30E2CF342FB2285816955634BE',
                    '883274A123A24F113E0A512C0EA45FF6')
bot = telebot.TeleBot('6482583581:AAHthRdJoDdogceNyFytENhMy7d9cnJ2iQs')
images={5389593084:None}
def send_image(message_id, text):
    global images
    images[message_id] = api.gen(text)
#send_image(5389593084,'Программист Никита')
#bot.send_photo(5389593084, images[5389593084],caption='Hi')

while 1:
    i=input('p:')
    filename = os.path.join('images', "1.jpg")  # Save the image in the specified directory
    with open(filename, "wb") as file:
        file.write(api.gen(i))
    print("Image created.")
#'''