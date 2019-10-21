# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 16:41:22 2019

@author: Onedas
"""

import json
import requests
from flask import Flask, request, Response
import intent_finder as IF
import pandas as pd
import sys

#%%global variables
API_KEY = '717912330:AAGxY2_sPeb-VziZpNEYkbmiEBq7BrUSU1k'

#%% URL
SEND_MESSAGE_URL = 'https://api.telegram.org/bot{token}/sendMessage'.format(token=API_KEY)
SEND_IMAGE_URL = 'https://api.telegram.org/bot{token}/sendPhoto'.format(token=API_KEY)

# %% data load and train # intent_finder
intent_finder = IF.Intent_Finder()
hello_finder = IF.Filter()

hello_data = ['안녕', '안뇽', '안녕하세요','안녕하세요','안녕하세요',
         '반갑다', '반가워', '반가워요', '반가워용', '반가웡', '반갑구만', 
         '반갑습니다', '반가반가', '반가',  '반갑구만 반가워', 
         '방갑다', '방가워', '방가방가', '방가워용', '방가웡', '방갑구만',
         '방갑습니다', '방가 방가', '방가', '방갑구만 방가워'
         'ㅎㅇ', 'ㅎㅇ요', '하이요', '하이', '하이루',
         '잘 지냈엉', '잘지냈엉', '잘지냈어', '잘 지냈어', '잘 지냈쪄', '잘지냈쪄',
         'hello', 'hi', '헬로우',
         '굳모닝', '굳 모닝', '굿모닝', '굿 모닝', 
         '굳이브닝', '굳 이브닝', '굿이브닝', '굿 이브닝', 
         '굳나잇', '굳 나잇', '굿나잇', '굿 나잇',
         '안녕하세요?', '안녕하세용', '안녕하세욤', '안녕하세영', 
         '안녕하세염', '안녕하십니까', '안녕하시렵니까',
         '좋은아침', '좋은 아침', '좋은 아침 입니다',
         '즐거운 하루', '즐거운하루', '좋은 하루', '좋은하루'
         '별일없지', '별일없징', '별일없찡',
         '쎼쎼', '쎄쎄', '쒜쒜', '쌔쌔', '니하오', '니 하오', '니하오마', '니 하오마',
         '오하요', '오하이오', '오하이요', '오하이요 고자이마스', '오하이오 고자이마스',
         '곤니치와', '곤니찌와', '곰방와', '곤방와'
         '/start']


DB_file = 'ds120FAQ.xlsx'
df = pd.read_excel(DB_file)

##
print('Train start')

count = 3
for _ in range(count):
    for hello in hello_data:
        hello_finder.fit(hello,'hello')

for i in range(len(df)):
#    category = df.loc[i][0] #카테고리 -> 행정
#    Q = df.loc[i][1] #
#    A = df.loc[i][2] #
    try:
        hello_finder.fit(df.loc[i][1],'Question')
        intent_finder.train(df.loc[i][1], df.loc[i][2], i)
        #break
    
    except Exception as ex: # 모든 예외를 catch 함
        print("오류내용: %s \n 오류발생 line: %s " % (ex, sys.exc_info()[-1].tb_lineno))

print('Load data : Done')

# %% function of backend
def text2hello_question(text):
    return hello_finder.predict(text)[0]

def text2Qnums(text):
    return intent_finder.find_answer(text)

def Qnum2Q(Qnum):
    s=''
    s+='[{}]Q{} : '.format(df.loc[Qnum][1],Qnum)+ df.loc[Qnum][2]
    
    return s        

def Qnum2A(Qnum):
    s=''
    s+='A : '+ df.loc[Qnum][3]
    return s

#print(Qnum2Q(282))
#print(Qnum2A(284))
print(intent_finder.find_answer('주정차 위반'))
#print(text2Qnums('강남구'))
#print(text2hello_question('하이'))
#print(intent_finder.big_filter.word_dict)
# %% function of telegram
app = Flask(__name__)

def parse_message(data):
    '''응답data 로부터 chat_id 와 text, user_name을 추출.'''
    chat_id = None
    msg = None
    user_name = None
    inline_data = None    
    
    if 'callback_query' in data:
        data=data['callback_query']
        inline_data = data['data']
        
    chat_id = data['message']['chat']['id']
    msg = data['message']['text']
    user_name = data['message']['chat']['first_name'] + data['message']['chat']['last_name']

    return chat_id, msg, user_name, inline_data    #https://core.telegram.org/bots/api#keyboardbutton


def send_message(chat_id, text):
    params = {'chat_id':chat_id, 'text': text}
    requests.post(SEND_MESSAGE_URL, json=params)

def send_message_keyboard(chat_id, text):
    keyboard = {'keyboard' : [[{'text': 'A'},{'text': 'B'}],
                              [{'text': 'C'},{'text': 'D'}]],
                'one_time_keyboard':True}
    
    params = {'chat_id':chat_id, 'text' : text, 'reply_markup':keyboard}
    requests.post(SEND_MESSAGE_URL, json=params)

def send_message_inlinekeyboard(chat_id,text,page=0):
    answer_nums = text2Qnums(text)
    print('answer num : ',answer_nums)
    text1 = Qnum2Q(answer_nums[0])
    text2 = Qnum2Q(answer_nums[1])
    text3 = Qnum2Q(answer_nums[2])
    InlineKeyboard = {'inline_keyboard' : [[{'text':text1, 'callback_data':answer_nums[0]}],
                                           [{'text':text2, 'callback_data':answer_nums[1]}],
                                           [{'text':text3, 'callback_data':answer_nums[2]}]]}

    params = {'chat_id':chat_id, 'text' : '{}에 대해 가장 유사도가 높은 답변 입니다'.format(text), 'reply_markup':InlineKeyboard}
    requests.post(SEND_MESSAGE_URL,json=params)
    

# %% main
# 경로 설정, URL 설정
@app.route('/', methods=['POST', 'GET'])
def main():
    if request.method == 'POST':
        message = request.get_json()
        with open('message.txt','w') as f:
            json.dump(message,f,indent=4)
        
        
        chat_id, msg, chat_name, inline_data = parse_message(message)
        print(msg, inline_data)
        if inline_data == None: # inline 버튼을 안눌렀을 때
            
            intent =  text2hello_question(msg)
            
            try:
                if intent == 'hello':
                    send_message(chat_id,'안녕하세요')
                    
                elif intent == 'Question':
                    send_message_inlinekeyboard(chat_id,msg)
            except:
                pass
        
        else: # inline 버튼을 눌렀을 때
            send_message(chat_id,Qnum2A(int(inline_data)))
            inline_data =None
            
       
        return Response('ok', status=200)
        
    else:
        return 'Hello World!'


if __name__ == '__main__':
    app.run(port = 5000)
