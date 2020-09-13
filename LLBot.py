# -*- coding: utf-8 -*-
import requests
import xml.dom.minidom
import json
import re


class BotController:
    
    def __init__(self,url,offset = None,timeout = 30):
        self.url = url
        self.offset = offset
        self.timeout = timeout
        self.qbaseUrl = 'https://db.chgk.info/xml/random/limit1'
        self.questions = {}
        self.answers = {}
        self.hints = {}
        self.scores = {}
        self.hiddenChar = u'\U0001F525'
    
    @property
    def commands(self):
        """
        creates dictionary to keep bot`s commands and thair handlers
        """
        comDic = {
            '/question'               :   lambda update: self.say(update['message']['chat']['id'],self.getQuestion(update)),
            '/question@LittleLokiBot' :   lambda update: self.say(update['message']['chat']['id'],self.getQuestion(update)),
            '/answer'                 :   lambda update: self.giveAnswer(update),
            '/answer@LittleLokiBot'   :   lambda update: self.giveAnswer(update),
            '/hint'                   :   lambda update: self.giveHint(update),
            '/hint@LittleLokiBot'     :   lambda update: self.giveHint(update),
            '/help'                   :   lambda update: self.showHelp(update),
            '/help@LittleLokiBot'     :   lambda update: self.showHelp(update),
            '/start'                  :   lambda update: self.showHelp(update),
            '/start@LittleLokiBot'    :   lambda update: self.showHelp(update),
            '/try'                    :   lambda update: self.checkAnswer(update),
            '/try@LittleLokiBot'      :   lambda update: self.checkAnswer(update),
            '/scores'                 :   lambda update: self.getScoresList(update),
            '/scores@LittleLokiBot'   :   lambda update: self.getScoresList(update),
        }
        return comDic
    
    def getUpd(self):
        """
        sends get request to api ussing its method "getUpdates" 
        with parameters timeout and offset which values initiate with bot construction
        returnes update if there is a new one
        """
        params = {'timeout': self.timeout, 'offset': self.offset}
        response = requests.get(self.url + 'getUpdates',params)
        results = response.json()
        result = results['result']
        if len(result)>0:
            return result[len(result)-1]
        else:
            return False;
        
    def say(self, chat_id, text):
        """
        sends a simple message (text) to chat (chatid)
        """
        params = {'chat_id': chat_id, 'text': text}
        resp = requests.post(self.url + 'sendMessage', params)
        return resp


        
    def getQuestion(self,update):
        """
        sends a get request to the base of questions 
        parses the response using xml.dom.minidom library
        saves question and answer in bot`s attributes
        returns the question
        prints the answer to console to make the bot holder the most clever person in any chat :)
        """
        chat = update['message']['chat']['id']
        
        if self.answers.get(chat):
            self.giveAnswer(update)
        
        response = requests.get(self.qbaseUrl)
        response.encoding = 'utf-8'
        result = xml.dom.minidom.parseString(response.text)
        question = result.getElementsByTagName('Question')[0].firstChild.data
        answer = result.getElementsByTagName('Answer')[0].firstChild.data
        
        self.questions[chat] = question
        self.answers[chat] = answer
        print(answer)
        return question
    
    def giveAnswer(self,update):
        """
        gives the answer for last asked question
        """
        chat = update['message']['chat']['id']
        
        if self.answers.get(chat):
            self.say(chat,self.answers[chat])
            del self.answers[chat]
            del self.questions[chat]
            if self.hints.get(chat):
                del self.hints[chat]
        else:
            self.say(chat,'Арррррг! Локи ничего не спрашивал! \n\n /help \n')
        
    def splitClearStr (self,string):
        """
        clears string of any punctuation
        makes and returns list of words        
        """
        string = string.lower()
        pattern=r'(/.*? )'
        string = re.sub(pattern,'',string)
        pattern=r'[,\.\!\-\?\[\]\{\}\(\)\"]'
        string = re.sub(pattern,'',string)
        string = string.split()
        print(string)
        return string
    
    def checkAnswer(self,update):
        answer = update['message']['text']
        chat = update['message']['chat']['id']
        user = update['message']['from']['first_name']
        print(answer, chat, user)
        """
        validates the answer
        trying to do it in subtle way
        splitting the user`s answer and right one, and checking number of includes
        """
        answerList = self.splitClearStr(answer)
        rightAnswerList = self.splitClearStr(self.answers[chat])
        includes = 0;
        for word in answerList:
            if word in rightAnswerList:
                includes+=1
        
        if includes>len(rightAnswerList)*0.4:
            points = self.getPoints(update)
            smile =  u'\U0000270C'		
            self.say(chat,f'Верно, {user}, продолжай в том же духе!\n\n     +   {points[0]} {smile}\n\n     Всего:  {points[1]}')
            self.giveAnswer(update)
        elif includes>len(rightAnswerList)*0.2:    
            self.say(chat,f'Локи сомневается, {user}, скажи другими словами!')
        elif includes>len(rightAnswerList)*0.1:    
            self.say(chat,f'Локи кажется, что это не полный ответ, {user}, попробуй дополнить!')
        else:    
            self.say(chat,f'Нет, {user}, определенно, нет...')
            
            
    def giveHint(self,update):
        """
        codes answer with symbols and shows them
        showes one more letter of the answer from the begining
        """
        chat = update['message']['chat']['id']
        
        if not self.answers.get(chat):
            self.say(chat,'Арррррг! Что еще подсказать?! \n\n /help')
            return False
        
        if not self.hints.get(chat):
            self.hints[chat] = re.sub(r'[a-zA-Zа-яА-ЯЁё]',self.hiddenChar,self.answers[chat])
        else:
            indx = self.hints[chat].index(self.hiddenChar)
            self.hints[chat] = self.answers[chat][:indx+1] + self.hints[chat][indx+1:]
        
        self.say(chat,self.hints[chat])
        return True

    def getPoints(self, update):
        """
        counts points for right answer
        """
        chat = update['message']['chat']['id']
        if not self.hints.get(chat):
            pts = len(self.answers[chat])*5
        elif self.hints[chat].index(self.hiddenChar)== 0:
            pts = len(self.answers[chat])*3
        else:
            pts = len(self.answers[chat])-self.hints[chat].index(self.hiddenChar)
        
        total = self.increaseScores(update,pts)['scores']    
        return [pts, total]    
        

    def increaseScores(self,update,pts):
        """
        increases user`s scores when user answers right
        """
        userCode = str(update['message']['from']['id'])
        name = update['message']['from']['first_name']
        
        try:
            lastname = update['message']['from']['last_name']
        except:
            lastname = "..."
        
        if self.scores.get(userCode):
            self.scores[userCode]['scores'] += pts
        else:        
            self.scores[userCode] = {'scores':pts, 'name':name, 'lastname':lastname}
        
        self.saveScores();
       
        
        return self.scores[userCode]   
    
    def getScoresList(self,update):
        """
        shows scores, leaderboard and the place user holds
        """
        smile =  u'\U000026A1'	
        user = update['message']['from']['id']
        userN = update['message']['from']['first_name']
        chat = update['message']['chat']['id']
        scores = self.scores[str(user)]['scores']
        
        scoresList = []
        for i in self.scores:
            scoresList.append(float(str(self.scores[i]['scores'])+'.'+str(i)))
            scoresList.sort(reverse = True)
        
        place = scoresList.index(float(f'{scores}.{user}'))+1
        
        h=0
        results = ''
        for j in scoresList:
            splitted = str(j).split('.')
            results += f'{smile}{self.scores[splitted[1]]["name"]} {self.scores[splitted[1]]["lastname"]}      {splitted[0]}\n'
            h+=1
            if h == 10:
                break
        
        self.say(chat,f'{userN}, у тебя {scores} очков!\n\nТы на {place}-м месте!\n\n Вот список лидеров:\n\n{results}')
    
    def handleReplay(self,update):
        """
        tries to get text from replied message
        or returns False
        """
        chat = update['message']['chat']['id']

        if 'reply_to_message' in update['message']:
            self.checkAnswer(update)
   
        else:            
            print('----> Не ответ ...')



    def saveScores(self):
        """
        saves scores
        """
        file = open('scores','w')
        file.write(json.dumps(self.scores))
        file.close()
        
    def loadScores(self):
        """
        tries to load scores from file
        """
        try:
            file = open('scores')
            content = file.read()
            self.scores = json.loads(content)
            print(self.scores)
            print('----> таблица очков успешно загружена')
        except:
            print('----> таблица очков не найдена')
            
            
            
    def handleCommand(self,update):
        """
        tryes to get command body from bot`s command list
        or returnes False
        """
   
        
        updList = update['message']['text'].split()
        
        if updList[0] in self.commands:
            command = self.commands[updList[0]]
            command(update)
        
        else:
            print('----> Не команда')
            
            
    def shiftOffset(self,update):
        """
        increases offset value 
        that is to use to making long polling according to api`s requairments
        """   
        self.offset = update['update_id']+1
    
    def showHelp(self, update):
        """
        sends simple help to the chat
        """
        chat = update['message']['chat']['id']
        text =  'Локи поможет разнообразить общение в чате, задавая интересные вопросы.\n'
        text += '\n'
        text += 'Для управления используйте следующие команды:\n'
        text += '/question  - получить вопрос\n'
        text += '/answer    - узнать ответ\n'
        text += '/hint      - получить подсказку\n'
        text += '/scores    - показать таблицу лидеров\n'
        text += '\n'
        text += 'Чтобы дать ответ на вопрос, ответьте на сообщение с вопросом,\n'
        text += '\n'
        text += 'или используйте    /try [ответ],\n'
        text += 'например           "/try Пушкин"\n'
        self.say(chat,text)
    
    def startPolling(self):
        """
        starts polling loop
        """
        
        self.loadScores()
        print('---> Локи начинает опрос чата на предмет обновлений...')
        
        while True:
            update = self.getUpd()
    
            if update:
                try:        
                    print('----> {} : {}'.format(update['message']['from']['first_name'],update['message']['text']))
                except KeyError:
                    print ('----> some uncought update')
                    
                self.handleCommand(update)
                self.handleReplay(update)
                self.shiftOffset(update)
        


llb = BotController("https://api.telegram.org/[botkey]]/")
llb.startPolling()


