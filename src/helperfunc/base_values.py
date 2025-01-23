import os
import redis
import json
from openai import OpenAI
import logging
from datetime import datetime

# Get the absolute path to the settings file
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

TOKEN_FILE = os.path.join(BASE_DIR, 'twitch_token.json')
CHANNEL_NAME = 'Beastyrabbit'
client = OpenAI()

# load redis
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)


# Function to load the token from a JSON file
def load_token():
	"""Load token from file if it exists."""
	_logger.debug(f'Loading token from {TOKEN_FILE}')
	if os.path.exists(TOKEN_FILE):
		with open(TOKEN_FILE) as file:
			return json.load(file)
	return None


def get_valid_token():
	"""Ensure a valid token is available, refreshing or re-authorizing if needed."""
	token_data = load_token()
	if token_data:
		expires_at = datetime.fromisoformat(token_data['expires_at'])
		if datetime.now() < expires_at:
			return token_data['access_token']  # Token is valid
		_logger.critical('Token expired, re-authorizing...')
		return None  # Token expired


def setup_logger(module_name: str):
	logger = logging.getLogger(module_name)
	logger.setLevel(logging.DEBUG)  # Set default level

	# Prevent duplicate logs
	if not logger.handlers:
		# Create a file handler
		actual_log_file = os.path.join(log_path, 'beatybot.log')
		file_handler = logging.FileHandler(actual_log_file)
		file_handler.setLevel(logging.INFO)

		# Create a console handler
		console_handler = logging.StreamHandler()
		console_handler.setLevel(logging.DEBUG)

		# Define formatter
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		file_handler.setFormatter(formatter)
		console_handler.setFormatter(formatter)

		# Add handlers
		logger.addHandler(file_handler)
		logger.addHandler(console_handler)

	return logger


# Logging is one folder up from the current file
log_path = os.path.join(BASE_DIR, 'logs')
# Create a logs directory if it doesn't exist
os.makedirs(log_path, exist_ok=True)
_logger = setup_logger(__name__)
