import requests
import json
import sys
from bottle import (  
    run, post, response, request as bottle_request
)

# Sub class
class Sub:
	def __init__(self, chat_id):
		self.chat_id = chat_id
		self.alert_level = 0

def load_subs(filename):
	try:
		file = open(filename, 'r')
	except FileNotFoundError:
		print('File ' + SUBS_FILE + ' not found')
		return

	sub_array = json.load(file)
	
	for i in range(0, len(sub_array)):
		chat_id = sub_array[i]['chat_id']
		sub = Sub(chat_id)
		sub.alert_level = sub_array[i]['alert_level']
		SUB_LIST[chat_id] = sub
	
	file.close()

def send_message(chat_id, message):
	# Create JSON body
	json_data = {}
	json_data["chat_id"] = chat_id
	json_data["text"] = message
	
	message_url = BOT_URL + 'sendMessage'
	requests.post(message_url, json=json_data)

# Globals

if len(sys.argv) < 3:
	print('Expected two arguments: token and message to be sent')
	exit()
	
API_TOKEN = sys.argv[1]
MESSAGE = sys.argv[2]
BOT_URL = 'https://api.telegram.org/bot' + API_TOKEN + '/'
SUB_LIST = {}
SUBS_FILE = 'subs.txt'

load_subs(SUBS_FILE)

for chat_id in SUB_LIST:
	send_message(chat_id, MESSAGE)
