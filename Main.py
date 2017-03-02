from flask import Flask, request
from twilio import twiml
from splinter import Browser
from twilio.rest import TwilioRestClient
import threading
import time


def text(client, message):
    client.messages.create(
        to=CLIENT_NUM,
        from=SERVER_NUM, #These are constants I define down there somewhere
        body=message
    )


def click_left(b):
	buttons = b.find_by_tag('button')
	buttons[7].click() #Idk why but there's invisible buttons. Index 7 is where the real ones start.

def click_right(b):
	buttons = b.find_by_tag('button')
	buttons[8].click()

def click_final(b, message):
    buttons = b.find_by_tag('button')
    looper = 0
    for char in message:
        if looper < 3: #There should only be 3 characters, but just in case.
            buttons[int(char) + 6].click() 
        else:
            pass
        looper += 1


def start_game(message_body, browser):
    browser.visit("http://jackbox.tv")
    message = message_body.split(" ")
    browser.find_by_id("roomcode").fill(message[0]) #Puts the code in the code box
    browser.find_by_id("username").fill(message[1]) #Puts the username in the username box
    browser.find_by_id("button-join").click()


def answer_question(message, browser):
    browser.find_by_id('quiplash-answer-input').fill(message)
    browser.find_by_id('quiplash-submit-answer').click()

#put try/except blocks in here.
#These try/excepts are horrible practice and should be fixed
def interpret(message, browser, client):
    action = message[0]
    message = message[1:]
    if action.lower() == 's':
        start_game(message, browser)
    elif action.lower() == 'a':
        try:
            answer_question(message, browser)
        except:
            text(client, "Couldn't answer question")
    elif action.lower() == 'v':
        try:
            if message == 'r': click_right(browser)
            elif message == 'l': click_left(browser)
        except:
            text(client, "Couldn't vote.")
    elif action.lower() == 'f':
        try:
            click_final(browser, message)
        except:
            text(client, "Couldn't final vote")
    else:
        text(client, "Didn't understand input.")


# put your own credentials here
ACCOUNT_SID = ""
AUTH_TOKEN = ""
CLIENT_NUM = '+11234567890'
SERVER_NUM = '+10987654321'

my_client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

browser = Browser() #Uses firefox by default.
browser_lock = threading.Lock() #These are so the browser and my_client variables aren't accessed by both threads at the same time

client_lock = threading.Lock()


class CheckerThread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    def run(self):
        global browser
        global my_client
        previous_questions = [''] #Basically, this runs as a loop, and I want it to text whenever it finds a question it HASN'T seen. There's a more elegant solution I'm sure
        while 1:
            browser_lock.acquire()
            try:
                question = browser.find_by_id('question-text').first.text
            except:
                question = ''
            browser_lock.release()
            if question not in previous_questions:
                print(question)
                client_lock.acquire()
                text(my_client, question)
                client_lock.release()
            previous_questions.append(question)
            time.sleep(2) # The 2 is arbitrary but some kinda sleep HAS to be here or it kills the processor





class FlaskThread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    def run(self):
        global browser
        global my_client
        app = Flask(__name__)


        @app.route('/sms', methods=['POST'])
        def sms():
            number = request.form['From']
            message_body = request.form['Body']
            browser_lock.acquire()
            client_lock.acquire()
            interpret(message_body, browser, my_client)
            browser_lock.release()
            client_lock.release()
            resp = twiml.Response()
            return str(resp)
        app.run()



if __name__ == '__main__':
    thread_1 = FlaskThread("flask")
    thread_2 = CheckerThread('checker')
    thread_1.start()
    thread_2.start()
    thread_1.join() #Idk if these need to be here but I saw a tutorial where they did. 
    thread_2.join()
