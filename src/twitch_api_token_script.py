import json
import os
from datetime import datetime, timedelta

import requests
from flask import Flask, request
from werkzeug.serving import run_simple

TOKEN_FILE = 'twitch_token.json'
REDIRECT_URI = 'https://twitchbot_recall.beasty.cloud/callback'
SCOPES = 'chat:read chat:edit moderator:manage:shoutouts moderator:manage:chat_settings moderator:manage:announcements'
CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

if CLIENT_ID is None or CLIENT_SECRET is None:
	raise ValueError('Please set the TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET environment variables')

app = Flask(__name__)


# Function to exchange the authorization code for an access token
def exchange_code_for_token(auth_code):
	"""Exchange the authorization code for an access token."""
	url = 'https://id.twitch.tv/oauth2/token'
	params = {
		'client_id': CLIENT_ID,
		'client_secret': CLIENT_SECRET,
		'code': auth_code,
		'grant_type': 'authorization_code',
		'redirect_uri': REDIRECT_URI,
	}
	response = requests.post(url, data=params)
	response.raise_for_status()
	token_data = response.json()
	save_token(token_data)
	return token_data['access_token']


# Function to save the token to a JSON file
def save_token(token_data):
	"""Save token to file."""
	token_data['expires_at'] = (datetime.now() + timedelta(seconds=token_data['expires_in'])).isoformat()
	with open(TOKEN_FILE, 'w') as file:
		json.dump(token_data, file)


# Function to load the token from a JSON file
def load_token():
	"""Load token from file if it exists."""
	if os.path.exists(TOKEN_FILE):
		with open(TOKEN_FILE) as file:
			return json.load(file)
	return None


# Function to refresh the token using the refresh token
def refresh_token(refresh_token):
	"""Refresh the token using the refresh token."""
	url = 'https://id.twitch.tv/oauth2/token'
	params = {
		'client_id': CLIENT_ID,
		'client_secret': CLIENT_SECRET,
		'grant_type': 'refresh_token',
		'refresh_token': refresh_token,
	}
	response = requests.post(url, data=params)
	response.raise_for_status()
	token_data = response.json()
	save_token(token_data)
	return token_data['access_token']


# Function to ensure a valid token exists
def get_valid_token():
	"""Ensure a valid token is available, refreshing or re-authorizing if needed."""
	token_data = load_token()

	if token_data:
		expires_at = datetime.fromisoformat(token_data['expires_at'])
		if datetime.now() < expires_at - timedelta(hours=1):
			return token_data['access_token']  # Token is valid
		print('Token expired. Refreshing...')
		return refresh_token(token_data['refresh_token'])

	# No token available; start authorization flow
	print('No valid token found. Please visit the following URL to authorize:')
	print('------------------------------------------------------------------')
	auth_url = f"https://id.twitch.tv/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES.replace(' ', '+')}"
	print(auth_url)
	print('------------------------------------------------------------------')
	run_server()  # Wait for user to authorize
	token_data = load_token()  # Load the token saved after exchange
	if not token_data:
		raise RuntimeError('Failed to retrieve token after authorization.')
	return token_data['access_token']


# Flask route to handle Twitch OAuth callback
@app.route('/callback')
def callback():
	"""Handle the redirect from Twitch and get the authorization code."""
	auth_code = request.args.get('code')
	if not auth_code:
		return 'Authorization failed. No code provided.', 400

	print(f'Authorization code received: {auth_code}')
	exchange_code_for_token(auth_code)  # Exchange for a token
	# Trigger server shutdown
	shutdown_server()
	return 'Authorization successful! You can close this page.'


# Function to start the Flask server
def run_server():
	"""Run the Flask server to handle OAuth callback."""
	print('Starting local server to handle Twitch OAuth...')
	run_simple('0.0.0.0', 5000, app)


# Function to shut down the Flask server
def shutdown_server():
	"""Shutdown the Flask server."""
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		print('Werkzeug server shutdown function not found. Exiting...')
		os._exit(0)  # Forcefully exit the process
	func()


# Main script
if __name__ == '__main__':
	access_token = get_valid_token()
	if access_token is None:
		raise ValueError('Failed to get access token')
	print(f'Access token: {access_token}')
