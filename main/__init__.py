import time
from datetime import datetime
import requests
from flask import request, Flask, render_template, Response
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
import nltk
from nltk.corpus import stopwords
from string import punctuation
import subprocess as sp
import json
import request_answers as ra
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
from sklearn.metrics import mean_squared_error, mean_absolute_error
import logging

nltk.download("stopwords")

app = Flask(__name__)

viber = Api(BotConfiguration(
    name='Jabka Bot',
    avatar='Jaba.png',
    auth_token='TOKEN'
))

logger = logging.getLogger(__name__)

FLAG = 1
MSE = None
na = []

'''<--------------MASHINE-LEARNING--------------------->'''

def reload():
    global cv, clf

    dataset_df = pd.read_csv('main/data/zkh-data.csv', names=["Theme", "Message"])
    dataset = dataset_df.astype({"Message": str, "Theme": int})

    russian_stopwords = stopwords.words("russian")

    def remove_punct(text):

        table = {33: ' ', 34: ' ', 35: ' ', 36: ' ', 37: ' ', 38: ' ', 39: ' ', 40: ' ', 41: ' ', 42: ' ', 43: ' ',
                  44: ' ', 45: ' ', 46: ' ', 47: ' ', 58: ' ', 59: ' ', 60: ' ', 61: ' ', 62: ' ', 63: ' ', 64: ' ',
                  91: ' ', 92: ' ', 93: ' ', 94: ' ', 95: ' ', 96: ' ', 123: ' ', 124: ' ', 125: ' ', 126: ' '}
        return text.translate(table)

    dataset['Message_clean'] = dataset['Message'].map(lambda x: x.lower())
    dataset['Message_clean'] = dataset['Message_clean'].map(lambda x: remove_punct(x))
    dataset['Message_clean'] = dataset['Message_clean'].map(lambda x: x.split(' '))
    dataset['Message_clean'] = dataset['Message_clean'].map(
        lambda x: [token for token in x if token not in russian_stopwords \
                    and token != " " \
                    and token.strip() not in punctuation])
    dataset['Message_clean'] = dataset['Message_clean'].map(lambda x: ' '.join(x))

    df_dataset = dataset[['Message_clean', 'Theme']]
    df_dataset_clean = df_dataset.loc[df_dataset['Theme'].isin([i for i in range(1, 40)])]
    df_dataset_clean.head()

    X = df_dataset_clean['Message_clean']
    y = df_dataset_clean['Theme']

    cv = CountVectorizer()
    X = cv.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

    clf = MultinomialNB()
    clf.fit(X_train, y_train)
    clf.score(X_test, y_test)
    
    predict = clf.predict(X_test)
    
    return mean_squared_error(predict, y_test)

@app.route('/message_theme_request/', methods=['POST', 'GET'])
def start():
    global FLAG, cv, clf, MSE
    
    is_start = open("./public_html/starter.txt", "r").read()
    
    if is_start == 'start':
    
        if FLAG == 1:
            MSE = reload()
            FLAG = 0
            time.sleep(1)
    
        if request.method == 'POST':
            msg = request.form['msg']
            vect = cv.transform([msg]).toarray()
            my_prediction = clf.predict(vect)
            
        elif request.method == 'GET':
            msg = request.args.get('msg')
            vect = cv.transform([msg]).toarray()
            my_prediction = clf.predict(vect)
            
        hello_time = {"21, 22, 23, 24, 0, 1, 2, 3, 4, 5": "???????????? ????????",
        "6, 7, 8, 9, 10": "???????????? ????????",
        "11, 12, 13, 14": "???????????? ????????",
        "16, 17, 18, 19, 20": "???????????? ??????????"}
    
        hour = int(datetime.now().strftime("%H"))    
        
        for i in hello_time:
            isp = list(map(int, i.split(', ')))
            if hour in isp:
                hello = hello_time[i]
            
        return json.dumps({"answer": ra.data[my_prediction[0] + 1],
        "theme": ra.data_d[my_prediction[0]], "mse": MSE, "hello": hello})
    else:
        return None

'''<--------------ADMIN--------------------->'''

@app.route('/no_answer/', methods=['POST'])
def no_answer():
    if request.method == 'POST':
        message = request.form['msg']
        ra.no_answers.append(message)
        
@app.route('/error/', methods=['GET'])
def err():
    global MSE, FLAG
    if FLAG == 1:
        MSE = reload()
        FLAG = 0
        time.sleep(1)
        
    return json.dumps({"mse": MSE})

@app.route('/right/', methods=['POST'])
def right_answer():
    global MSE
    if request.method == 'POST':
        message = request.form['msg']
        theme = ra.data_r[request.form['theme']]
        dataset = pd.read_csv('main/data/zkh-data.csv', names=["Theme", "Message"])
        datacsv = open('main/data/zkh-data.csv', 'r')
        datacsv.write(f'\n{len(dataset.index)},{theme},{message}')
        datacsv.close()
        MSE = reload()

@app.route('/admin_panel/', methods=['POST', 'GET'])
def admin_panel():

    if request.method == 'POST':
        starter = open('public_html/starter.txt', 'w')
        if request.form['name'] == '??????????':
            starter.write("start")
        elif request.form['name'] == '????????':
            starter.write("stop")
        starter.close()
    return render_template('admpanel.html')

@app.route('/bot/', methods=['POST', 'GET'])
def phpvkbot():
    out = sp.run(["php", "public_html/vkTESTbot.php"], stdout=sp.PIPE)
    return out.stdout
    
@app.route('/teste/', methods=['GET', 'POST'])
def testet():
    if request.method == 'GET':
        message = request.args.get('msg')
        answer = requests.get(f'message_theme_request/?msg={message}')
        return answer.json()
        
@app.route('/rasp/', methods=['GET'])
def rasp():
    return {'list': ra.no_answers}

'''<--------------VIBER--------------------->'''

@app.route('/viber_bot/', methods=['POST'])
def viber_bot():
    
    logger.debug("received request. post data: {0}".format(request.get_data()))
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberMessageRequest):
        message = viber_request.message.text
        answer = requests.get(f'message_theme_request/?msg={message}')
        #msg = "????????????! ???????? ?????? ?????? ?? ????????????????????!"
        viber.send_messages(viber_request.sender.id,
        TextMessage(text=str(answer.json()['hello'])))
        viber.send_messages(viber_request.sender.id,
        TextMessage(text=str(answer.json()['answer'])))
        viber.send_messages(viber_request.sender.id,
        TextMessage(text="?????? ?????????????? ???????? ???????????\n[????/??????]"))
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.get_user.id, [
            TextMessage(text=str("answer"))
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        logger.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)

if __name__ == '__main__':
    context = ('server.crt', 'server.key')
    app.run(host='0.0.0.0', port=443, ssl_context=context)