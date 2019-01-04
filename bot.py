#!/usr/bin/python3

import requests
import json
import sys
import _thread

from bottle import (  
    run, post, response, request as bottle_request
)

# Globals
	
API_TOKEN = sys.argv[1]
BOT_URL = 'https://api.telegram.org/bot' + API_TOKEN + '/'
SUB_LIST = {}
SUBS_FILE = 'subs.txt'
CISCO_OFFSET = 184


# Debug	
def log_command(command):
	print('Recieved ' + command + ' command')
	
# Message handling

def get_message_text(data):
	message = data['message']
	
	if 'text' in message:
		return message['text']

def send_message(chat_id, message):
	# Create JSON body
	json_data = {}
	json_data["chat_id"] = chat_id
	json_data["text"] = message
	
	message_url = BOT_URL + 'sendMessage'
	requests.post(message_url, json=json_data)
	
def get_chat_id(data):  
    chat_id = data['message']['chat']['id']

    return chat_id
	
# Command handling
	
def is_command(data):

	if 'message' in data:
		message = data['message']

		if 'entities' in message:

			type = message['entities'][0]['type']

			if type == 'bot_command':
				return True
			
	return False

def get_command_and_args(command_line):
	
	command = command_line.split(' ', 1)[0]
	args = command_line.split(' ')
	args.remove(command)

	return command, args
	
def handle_command(command, args, data):
	
	chat_id = get_chat_id(data)
	
	if command == '/sub':
		log_command(command)
		
		result = add_sub(chat_id)
		
		if result:
			message = str(chat_id) + ' Added to the subs list'
			save_subs(SUBS_FILE)
		else:
			message = str(chat_id) + ' Was not added: It was already present on the list'

	elif command == '/unsub':
		log_command(command)
		
		result = del_sub(chat_id)
		
		if result:
			message = str(chat_id) + ' Removed from the subs list'
			save_subs(SUBS_FILE)
		else:
			message = str(chat_id) + ' Was not removed: It wasn\'t present on the list'
	
	elif command == '/set_alert_level':
		log_command(command)
		
		if len(args) > 0:
			try:
				alert_level = int(args[0])
				
				result = set_alert_level(chat_id, alert_level)
		
				if result:	
					message = 'Alert-level has been set to ' + str(alert_level)
				else:
					message = 'Alert-level could not be set, you are no suscribed'
				
			except ValueError:
				message = 'Invalid argument : alert_level'
		else:
			message = 'Missing argument: alert_level'
			
	else:
		message = 'Not a valid command: ' + command
		message = message + '\nAvailable commands: \nsub\nunsub\nset_alert_level'
		
	send_message(chat_id, message)
	print(message)
	
	return

def should_recieve_alert(chat_id, alert_level):
	return alert_level <= SUB_LIST[chat_id].alert_level 
		

# Sub Command handling
def add_sub(chat_id):
	if chat_id in SUB_LIST:
		return False
	else:
		sub = Sub(chat_id)
		
		SUB_LIST[chat_id] = sub
		return True
	
def del_sub(chat_id):
	if chat_id in SUB_LIST:
		SUB_LIST.pop(chat_id, None)
		return True
	return False

# Set-alert-level  Command handling
def set_alert_level(chat_id, level):
	
	if chat_id in SUB_LIST:
		sub = SUB_LIST[chat_id]
		sub.alert_level = level
		return True
	else:
		return False
	
def get_alert_level_from_log_msg(msg):
	sub_str = msg.split(']')[0]
	str_alert_lvl = sub_str.replace('[', '')
	alert_level = int(str_alert_lvl) - CISCO_OFFSET
	
	print(alert_level)
	
	return alert_level
	
# File handling
def save_subs(filename):
	file = open(filename, 'w+')
	
	json.dump([SUB_LIST[sub].__dict__ for sub in SUB_LIST], file)
		
	file.close()

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
	
# Sub class
class Sub:
	def __init__(self, chat_id):
		self.chat_id = chat_id
		self.alert_level = 7
	
# Server
def init_server():
	run(host='localhost', port=8080, debug=True)

# Read from syslog-ng data
def read_log_messages():
	while True:
		# Get log messages
		log_msg = input()
		# Broadcast to every subscriber
		for chat_id in SUB_LIST:
			alert_lvl = get_alert_level_from_log_msg(log_msg)
			if should_recieve_alert(chat_id, alert_lvl):
				send_message(chat_id, log_msg)
	
@post('/')
def main():  
	# Get JSON Data
	data = bottle_request.json
	
	# Handle request
	if is_command(data):
		command_line = get_message_text(data)
		command, args = get_command_and_args(command_line)
		handle_command(command, args, data)
	else:
		print('Not a command')
	
	return response  # status 200 OK by default

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print('Expected one telegram token argument')
		exit()
	load_subs(SUBS_FILE)
	_thread.start_new_thread(read_log_messages, ())
	init_server()
	