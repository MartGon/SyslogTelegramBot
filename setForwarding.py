import requests
import sys

if len(sys.argv) < 3:
		print('Expected one telegram token argument and one redirection URL')
		exit()

# Parse arguments
API_TOKEN = sys.argv[1]
Ngrok = sys.argv[2]

BOT_URL = 'https://api.telegram.org/bot' + API_TOKEN + '/'
URL = BOT_URL + 'setWebHook?url=' + Ngrok + '/'

print(URL)

requests.get(URL)