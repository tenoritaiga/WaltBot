# RESOURCE: http://www.apnorton.com/blog/2017/02/28/How-I-wrote-a-Groupme-Chatbot-in-24-hours/


# IMPORTS
import os, json, requests
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from flask import Flask, request
from flask.json import jsonify
from pprint import pformat
from time import time
import arrow
import redis

app = Flask(__name__)
client_id = os.environ.get('CLIENT_ID')
refresh_token = os.environ.get('REFRESH_TOKEN')
redirect_uri = "https://waltbot-groupme.herokuapp.com"
authorization_base_url = "https://auth.tdameritrade.com/auth"
token_url = "https://api.tdameritrade.com/v1/oauth2/token"

bot_id = "REPLACE THIS WITH YOUR BOT ID ONCE BOT IS ADDED TO THE CHAT"

# Connect to redis
r = redis.from_url(os.environ.get("REDIS_URL"))
r.set('auth_token','none')
r.set('auth_timestamp','2010-01-01T00:01:10.490919+00:00')


# Called whenever the app's callback URL receives a POST request
# That'll happen every time a message is sent in the group
@app.route('/', methods=['POST'])
def webhook():
	# 'message' is an object that represents a single GroupMe message.
	message = request.get_json()

	# TODO: Your bot's logic here

	return "ok", 200
    
@app.route('/', methods=['GET'])
def test():
    auth_token = r.get('auth_token').decode('utf-8')
    
    # If the token is stale, request a new one and store it along with the
    # timestamp of when we requested it
    timestamp = r.get('auth_timestamp').decode('utf-8')
    if arrow.get(timestamp) < (arrow.utcnow().shift(minutes=-30)):
        print("requesting a new auth token")
        auth_token = get_new_auth_token()
        r.set('auth_token',str(auth_token).encode('utf-8'))
        r.set('auth_timestamp',str(arrow.utcnow()).encode('utf-8'))
        
    return auth_token
        

################################################################################

def get_new_auth_token():
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    data = { 'grant_type': 'refresh_token', 'refresh_token': refresh_token, 'access_type': 'offline', 'client_id': client_id, 'redirect_uri': redirect_uri}
    resp = requests.post(token_url,headers=headers,data=data)
    print(resp.json())
    return resp.json()['access_token']

# Send a message in the groupchat
def reply(msg):
	url = 'https://api.groupme.com/v3/bots/post'
	data = {
		'bot_id'		: bot_id,
		'text'			: msg
	}
	request = Request(url, urlencode(data).encode())
	json = urlopen(request).read().decode()

# Send a message with an image attached in the groupchat
def reply_with_image(msg, imgURL):
	url = 'https://api.groupme.com/v3/bots/post'
	urlOnGroupMeService = upload_image_to_groupme(imgURL)
	data = {
		'bot_id'		: bot_id,
		'text'			: msg,
		'picture_url'		: urlOnGroupMeService
	}
	request = Request(url, urlencode(data).encode())
	json = urlopen(request).read().decode()
	
# Uploads image to GroupMe's services and returns the new URL
def upload_image_to_groupme(imgURL):
	imgRequest = requests.get(imgURL, stream=True)
	filename = 'temp.png'
	postImage = None
	if imgRequest.status_code == 200:
		# Save Image
		with open(filename, 'wb') as image:
			for chunk in imgRequest:
				image.write(chunk)
		# Send Image
		headers = {'content-type': 'application/json'}
		url = 'https://image.groupme.com/pictures'
		files = {'file': open(filename, 'rb')}
		payload = {'access_token': 'eo7JS8SGD49rKodcvUHPyFRnSWH1IVeZyOqUMrxU'}
		r = requests.post(url, files=files, params=payload)
		imageurl = r.json()['payload']['url']
		os.remove(filename)
		return imageurl

# Checks whether the message sender is a bot
def sender_is_bot(message):
	return message['sender_type'] == "bot"
