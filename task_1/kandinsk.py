import requests
import json
import time
import base64
import os
import re

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

nlp = spacy.load("ru_core_news_sm")
def main_part(text):
    doc = nlp(text)
    sentences = list(doc.sents)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([sentence.text for sentence in sentences])
    tfidf_scores = tfidf_matrix.toarray()
    max_index = tfidf_scores.sum(axis=1).argmax()
    best_sentence = sentences[max_index].text
    if len(best_sentence) > 600:
        best_sentence = best_sentence[:600]
    if len(best_sentence) < 500:
        additional_sentence = ""
        for i in range(max_index + 1, len(sentences)):
            additional_sentence += sentences[i].text + " "
            if len(best_sentence) + len(additional_sentence) >= 500:
                break
        best_sentence += additional_sentence.strip()
    print('s'+best_sentence.strip()+'e')
    return best_sentence.strip()

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
        #summary = model( summary=text
        prompt = main_part(text)

        prompt+=' Создай позитивную футуристическую иллюстрацию. --no text'
        model_id = self.get_model()
        uuid = self.generate(prompt, model_id)
        images = self.check_generation(uuid)

        if images and len(images) > 0:
            image_base64 = images[0]

            image_data = base64.b64decode(image_base64)
            return image_data


'''api = Text2ImageAPI('https://api-key.fusionbrain.ai/', 'FFF38A30E2CF342FB2285816955634BE',
                    '883274A123A24F113E0A512C0EA45FF6')


while 1:
    i=input('p:')
    filename = os.path.join('', "1.jpg")
    with open(filename, "wb") as file:
        file.write(api.gen(i))
    print("Image created.")
#'''