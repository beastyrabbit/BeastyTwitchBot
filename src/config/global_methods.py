import os
import random
from datetime import datetime

import numpy as np

from config.base_values import client, redis_client, setup_logger
from objects.setting import OfficialCommands, SettingsManager
from objects.user import User

_logger = setup_logger(__name__)

global_settings_Manager: SettingsManager = SettingsManager()


def inc_global_chat_counter():
	redis_client.hincrby('stream:global', 'messege_counter', 1)


def calculate_interest(user: User):
	# check if user has invested before
	if user.points_invested == 0:
		return 0
	# get the amount of points invested
	invested = int(user.points_invested)
	# get the timestamp
	timestamp = user.timestamp_investment
	# rate is 0.02
	daily_interest_rate = global_settings_Manager.getCommand(OfficialCommands.invest).daily_interest_rate
	# calcautlte the days since investment in days
	current_time = datetime.utcnow()
	timestamp = datetime.fromisoformat(timestamp)
	days_since_investment = (current_time - timestamp).days
	if days_since_investment == 0:
		return 0

	# Calculate compound interest daily
	total_amount = invested * (1 + daily_interest_rate) ** days_since_investment
	# round down to 0 decimal points
	total_amount = int(total_amount)
	interest = total_amount - invested
	# store the add collected interest in the database for the user
	# check if user has collected interest before
	user.points_collected_from_investment += interest
	user.timestamp_investment = current_time.isoformat()

	# Return total balance including interest
	return interest


def get_discussion_topic_for_technology():
	# Get the last 10 discussion topics
	last_topics = redis_client.lrange('discussion_topics', -10, -1)
	last_topics = [topic for topic in last_topics]
	# Generate a new topic
	completion = client.chat.completions.create(
		model='gpt-4o-mini',
		messages=[
			{
				'role': 'user',
				'content': f"Generate a unique discussion topic about technology. Don't use highly philosophical question, a bit is ok. It should only be one Sentence/Question Avoid these topics: {', '.join(last_topics)}",
			}
		],
	)
	new_topic = completion.choices[0].message.content.strip()

	# Add the new topic to Redis
	redis_client.rpush('discussion_topics', new_topic)

	# Print the new unique topic
	return new_topic


def let_ai_narrate_the_fight(fight_sequence):
	# Convert the fight sequence into a readable log
	formatted_fight = '\n'.join(fight_sequence)

	# Call the AI model to narrate the fight
	completion = client.chat.completions.create(
		model='gpt-4o-mini',
		messages=[
			{
				'role': 'user',
				'content': (
					'The Narrator should do a very short battle report. like max 3 short sentences' 'Include dramatic flair, intense emotions, and heroic descriptions. ' "Here's the fight log:\n\n" f'{formatted_fight}'),
			}
		],
		max_tokens=300,
		temperature=0.7,
	)

	return completion.choices[0].message.content.strip()


def get_text_to_spech(text: str, output_name: str = 'output', voice: str = 'onyx', hd: bool = False):
	# Text-to-Speech
	if hd:
		modeltype = 'tts-1-hd'
	else:
		modeltype = 'tts-1'

	response = client.audio.speech.create(
		model=modeltype,
		voice=voice,  # Choose from available voices: alloy, echo, fable, onyx, shimmer
		input=text,
	)
	# Save the audio output into folder AUDIO_PATH
	AUDIO_PATH = f'/data/twitchbot/audio/{output_name}_audio.mp3'
	# check filde exists and delete it
	if os.path.exists(AUDIO_PATH):
		os.remove(AUDIO_PATH)

	response.stream_to_file(AUDIO_PATH)


def translate_text(text):
	completion = client.chat.completions.create(
		model='gpt-4o-mini',
		messages=[
			{
				'role': 'user',
				'content': f"Figure out the langauge for this input: '{text}' if its english translate it to german and if its german translate it to english."
				           ' Your answer should be very short. If its a sentence translate the sentence. If the translation is not 1 to 1 add a super extra soft explanation.',
			}
		],
	)
	return completion.choices[0].message.content.strip()

	# Ensure store_value is an integer
	store_value = int(store_value)

	# Check if the user already exists in the Redis hash
	if not redis_client.hexists(redis_key, username):
		# Initialize the user's value to 0 if not present
		redis_client.hset(redis_key, username, 0)

	# Increment the value for the username
	redis_client.hincrby(redis_key, username, store_value)

	# Increment the total count for the command
	redis_client.hincrby(count_key, username, 1)

	# Update the timestamp in the separate hash
	current_time = datetime.utcnow().isoformat()
	redis_client.hset(timestamp_key, username, current_time)
	logger.debug(
		f'Updated Redis -> Chat command: {chat_command}, Username: {username}, Incremented by: {store_value}, Time: {current_time}')


def do_the_cleaning_command(user: User) -> tuple[int, bool]:
	# Get the random value
	if global_settings_Manager.check_user_not_in_timeout(user, OfficialCommands.roomba):
		max_value = global_settings_Manager.getCommand(OfficialCommands.roomba).current_max_value
		get_random = random.randint(1, max_value)
		_logger.info(
			f'{user.username} cleaned up {get_random} from a max of {global_settings_Manager.getCommand(OfficialCommands.roomba).current_max_value}')
		# we will store the person who hit the max value
		if get_random == max_value:
			# check if user has max value hit before
			user.clean_max_hit_counter += 1
			global_settings_Manager.getCommand(OfficialCommands.roomba).current_max_value *= 10
		# Store the cleaned value in a database
		user.clean_points_collected += get_random
		# Store the amount of messages cleaned up in a database
		return get_random, get_random == max_value
	return 0, False


def generate_rnd_amount_to_steal() -> int:
	# Pre-configured parameters
	max_value = global_settings_Manager.getCommand(OfficialCommands.roomba).current_max_value
	luck_factor = 20.0  # Higher values make high numbers less likely

	# Create a range of possible values
	values = np.linspace(0, max_value, 1000)

	# Define weights: Exponentially decrease probability for higher values
	weights = np.exp(-luck_factor * (values / max_value))
	weights /= weights.sum()  # Normalize to sum to 1

	# Generate a single result
	result = np.random.choice(values, size=1, p=weights)
	return int(result[0])
