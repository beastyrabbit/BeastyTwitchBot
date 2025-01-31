import asyncio
import random
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytz
from twitchio.ext import commands

from helperfunc.global_methods import inc_global_chat_counter, let_ai_narrate_the_fight
from helperfunc.base_values import CHANNEL_NAME, get_valid_token, setup_logger
from helperfunc.object_manager import ObjectManager
from helperfunc.object_manager import UserManager

_logger = setup_logger(__name__)


class Bot(commands.Bot):

	def __init__(self):
		# Initialise our Bot with our access token, prefix and a list of channels to join on boot...
		# prefix can be a callable, which returns a list of strings or a string...
		# initial_channels can also be a callable which returns a list of strings...
		access_token = get_valid_token()

		self.object_manager = ObjectManager()
		self.user_manager: UserManager = self.object_manager.user_manager

		self.number_of_send_messages = 0
		super().__init__(token=access_token, prefix='!', initial_channels=[CHANNEL_NAME])

	async def event_command_error(self, context: commands.Context, error: Exception):
		if isinstance(error, commands.CommandNotFound):
			return

		if isinstance(error, commands.ArgumentParsingFailed):
			await context.send(error.message)

		elif isinstance(error, commands.MissingRequiredArgument):
			await context.send("You're missing an argument: " + error.name)

		elif isinstance(error, commands.CheckFailure):  # we'll explain checks later, but lets include it for now.
			await context.send('Sorry, you cant run that command: ' + error.args[0])

		#
		# elif isinstance(error, YoutubeConverterError):
		#  await context.send(f'{error.link} is not a valid youtube URL!')

		else:
			_logger.error(error)

	async def event_ready(self):
		# Notify us when everything is ready!
		# We are logged in and ready to chat and use commands...
		_logger.info(f'Logged in as | {self.nick}')
		_logger.info(f'User id is | {self.user_id}')
		await self.get_channel(CHANNEL_NAME).send("Viewer Bot ready to service!")

	async def event_message(self, message):
		# Messages with echo set to True are messages sent by the bot...
		# For now we just want to ignore them...
		if message.echo:
			return

		# Print the contents of our message to console...
		_logger.info(f'Chat: {message.author.name} | {message.content}')
		if not self.user_manager.check_user_exists(message.author.name):
			self.user_manager.create_user(message.author.name)
			# write welcome message to chat for first message
			await message.channel.send(f'Welcome to the chat {message.author.name}! 🐰')
		user = self.user_manager.get_user(message.author.name)
		user.global_chats_send += 1

		# add one to reddis message count
		inc_global_chat_counter()

		# Since we have commands and are overriding the default `event_message`
		# We must let the bot know we want to handle and invoke our commands...
		await self.handle_commands(message)

	@commands.command(name='points', aliases=('stats', 'dustbunnies'))
	async def points_command(self, ctx: commands.Context, username: str = None):
		_logger.info(f'{ctx.author.name} is checking points')
		if username:
			# remove username if its @
			if '@' in username:
				username = username[1:]
		username = username or ctx.author.name
		username = username.lower()
		# we want to give alll stts for the user
		# clean stats
		user = self.user_manager.get_user(username)

		sum_cleaned = user.clean_points_collected
		commands_send = user.command_count
		await ctx.send(f'{username} has cleaned up 🐰 {sum_cleaned} Dustbunnies in a total of {commands_send} messages!')
		# gamble stats
		sum_gambled = user.gambling_input
		sum_gamble_results = user.gambling_results
		await ctx.send(
			f'{username} has gambled 🎰 {sum_gambled} Dustbunnies and won/lost {sum_gamble_results} Dustbunnies!')
		# investment stats
		sum_invested = user.points_invested
		sum_interest_collected = user.points_collected_from_investment
		last_collectd = user.timestamp_investment
		# last collected in fomat MM/DD/YYYY
		last_collectd = datetime.fromisoformat(last_collectd).strftime('%m/%d/%Y')
		await ctx.send(f'{username} has invested 💰 {sum_invested} Dustbunnies and collected {sum_interest_collected}!')
		await ctx.send(f'{username} last collected interest on {last_collectd}!')

	@commands.command(name='hello', aliases=('hi', 'hallo'))
	async def hello_command(self, ctx: commands.Context):
		_logger.info(f'{ctx.author.name} is saying hello')
		# Here we have a command hello, we can invoke our command with our prefix and command name
		# e.g ?hello
		# We can also give our commands aliases (different names) to invoke with.

		# Send a hello back!
		# Sending a reply back to the channel is easy... Below is an example.
		await ctx.send(f'Hello @{ctx.author.name}!')

	# lurk
	@commands.command(name='lurk')
	async def lurk_command(self, ctx: commands.Context):
		_logger.info(f'{ctx.author.name} is lurking')
		# store send command in redis for user
		user = self.user_manager.get_user(ctx.author.name)
		user.lurk_counter += 1
		# Inform the chat about the timer being set
		await ctx.send(
			f'{ctx.author.name} will be watching for the {user.lurk_counter} time from the shadows. Thank you for lurking. 🐰🐻')

	# suika
	@commands.command(name='suika')
	async def suika_command(self, ctx: commands.Context):
		_logger.info(f'{ctx.author.name} is calling the suika command')
		# Inform the chat about the timer being set
		await ctx.send(
			' You can plasy Suika by typing !join. When its your turn put 0-100 in chat. If you want to leave the game type !leave. 🍉🍉🍉')

	@commands.command(name='timezone')
	async def timezone_command(self, ctx: commands.Context, custom_timezone: str = None):
		if custom_timezone:
			_logger.info(f'{ctx.author.name} is checking the timezone for {custom_timezone}')
			custom_timezone = custom_timezone.upper()
			if custom_timezone == 'CST':
				custom_timezone = 'CST6CDT'
			if custom_timezone == 'EST':
				custom_timezone = 'EST5EDT'
			if custom_timezone == 'PST':
				custom_timezone = 'PST8PDT'

		else:
			_logger.info(f'{ctx.author.name} is checking the timezone')

		try:
			# Always display German timezone
			german_timezone = pytz.timezone('Europe/Berlin')
			german_time = datetime.now(german_timezone).strftime('%H:%M:%S')
			is_dst = german_timezone.localize(datetime.now()).dst() != timedelta(0)
			german_timezone_name = 'Central European Summer Time (CEST)' if is_dst else 'Central European Time (CET)'

			await ctx.send(f'The current time in Germany is {german_time} ({german_timezone_name})')

			# Handle optional custom timezone
			if custom_timezone:
				try:
					if custom_timezone.upper().startswith('GMT'):
						offset = int(custom_timezone[3:])
						target_timezone = pytz.FixedOffset(offset * 60)
						timezone_display_name = f'GMT{offset:+}'
					else:
						target_timezone = pytz.timezone(custom_timezone)
						timezone_display_name = custom_timezone

					custom_time = datetime.now(target_timezone).strftime('%H:%M:%S')
					is_dst_custom = target_timezone.localize(datetime.now()).dst() != timedelta(0) if hasattr(
						target_timezone, 'localize') else False
					dst_status = ' (DST Active)' if is_dst_custom else ''
					await ctx.send(f'The current time in {timezone_display_name} is {custom_time}{dst_status}.')

				except pytz.UnknownTimeZoneError:
					await ctx.send(
						f'Invalid timezone: {custom_timezone}. Please use valid names like "GMT+7", "CET", "PST".')
		except Exception as e:
			_logger.error(f'Error in timezone command: {e}')
			await ctx.send('An error occurred while processing the timezone. Please try again.')

	@commands.command(name='fight', aliases=('battle', 'duel', 'flight'))
	async def fight_command(self, ctx: commands.Context, username: str):
		_logger.info(f'{ctx.author.name} is requesting a fighting with {username}')
		if not username:
			await ctx.send(f'@{ctx.author.name} Please provide a username to fight with.')
			return

		if '@' in username:
			username = username[1:]
		username = username.lower()

		# save the fighting request pair to have it in the database for later
		# there can only be one request at a time for a username
		user = self.user_manager.get_user(username)
		user.fight_requested_by = ctx.author.name

		# Request a fight with the other user
		await ctx.send(f'@{username} {ctx.author.name} has requested a fight with you! Type !accept to fight back!')

	@commands.command(name='accept')
	async def accept_command(self, ctx: commands.Context, username: str = None):
		_logger.info(f'{ctx.author.name} is accepting a fight')
		if username and not ctx.author.is_mod:
			return
		# Check if the user has a pending fight request
		if username:
			if '@' in username:
				username = username[1:]
			username = username.lower()
			opponent = username
		else:
			opponent = self.user_manager.get_user(ctx.author.name).fight_requested_by
			if not opponent:
				# await ctx.send(f'@{ctx.author.name} You do not have any pending fight requests.')
				_logger.warning(f"User: {ctx.author.name} tryed to accept a fight but no oppenent found")
				return

		# Remove the fight request
		self.user_manager.get_user(ctx.author.name).clear_fight_requested_by()

		# Start the fight
		await ctx.send(f'@{ctx.author.name} has accepted the fight with @{opponent}! Let the battle begin!')

		# give both users a helth value between 70-100
		# give both a weapon with dmg between 5-20 and a hit chance between 70-100
		opponent_health = random.randint(70, 100)
		opponent_weapon = {'dmg': random.randint(5, 20), 'hit_chance': random.randint(70, 100)}
		user_health = random.randint(70, 100)
		user_weapon = {'dmg': random.randint(5, 20), 'hit_chance': random.randint(70, 100)}
		_logger.info(f'@{opponent} has {opponent_health} health and a weapon with {opponent_weapon}')
		_logger.info(f'@{ctx.author.name} has {user_health} health and a weapon with {user_weapon}')

		# start the fight and write an array for the log and the person how won
		fight_log = []
		winner = None
		while True:
			# check if the user or the opponent has a hit
			if random.randint(1, 100) <= user_weapon['hit_chance']:
				opponent_health -= user_weapon['dmg']
				fight_log.append(
					f'@{ctx.author.name} hits @{opponent} with {user_weapon["dmg"]} damage. @{opponent} has {opponent_health} health left.')
				if opponent_health <= 0:
					fight_log.append(
						f'@{ctx.author.name} has won the fight against @{opponent} with {user_health} health left.')
					winner = ctx.author.name
					break
			else:
				fight_log.append(
					f'@{ctx.author.name} misses @{opponent}. @{opponent} has {opponent_health} health left.')
			if random.randint(1, 100) <= opponent_weapon['hit_chance']:
				user_health -= opponent_weapon['dmg']
				fight_log.append(
					f'@{opponent} hits @{ctx.author.name} with {opponent_weapon["dmg"]} damage. @{ctx.author.name} has {user_health} health left.')
				if user_health <= 0:
					fight_log.append(
						f'@{opponent} has won the fight against @{ctx.author.name} with {opponent_health} health left.')
					winner = opponent
					opponent = ctx.author.name
					break
			else:
				fight_log.append(
					f'@{opponent} misses @{ctx.author.name}. @{ctx.author.name} has {user_health} health left.')
		_logger.debug(fight_log)
		_logger.info(f'{winner} has won the fight against {opponent}')
		# send the fight log
		ai_message = let_ai_narrate_the_fight(fight_log)
		_logger.debug(ai_message)
		# split the message at 450 characters to not exceed the twitch message limit loop over it to get it out
		for i in range(0, len(ai_message), 450):
			await ctx.send(ai_message[i: i + 450])

		# winner is and deffiet the looser
		await ctx.send(f'@{winner} has won the fight against @{opponent}! 🎉')
		# track who won the fight
		self.user_manager.get_user(opponent).fights_lost += 1
		self.user_manager.get_user(winner).fights_won += 1

	# timer
	@commands.command(name='timer')
	async def timer_command(self, ctx: commands.Context, type: str, time: int):
		_logger.info(f'User {ctx.author.name} requested a {type} timer for {time} minutes.')
		time_in_seconds = time * 60
		try:
			# Inform the chat about the timer being set
			await ctx.send(f'{type.capitalize()} Timer set for {time} minute(s) 🤖 !')

			# 2 min left on timer
			await asyncio.sleep(time_in_seconds - 120)
			await ctx.send(f'@{ctx.author.name} your {type.capitalize()} Timer has 2 minutes left! 🚨')

			# Wait for the specified time
			await asyncio.sleep(time_in_seconds)

			# Notify the chat that the timer is up
			await ctx.send(f'@{ctx.author.name} your {type.capitalize()} Timer is up! 🚨')
		except ValueError:
			# Handle invalid input gracefully
			await ctx.send('Invalid time value. Please specify the time in minutes (e.g., !timer focus 5).')

	@commands.command(name='command', aliases=('commands'))
	async def command_command(self, ctx: commands.Context):
		_logger.info(f'{ctx.author.name} is calling the command command')
		# List all the possible commands
		await ctx.send('List of commands: !roomba, !points, !brb, !timer, !lurk')
		await ctx.send('!suika, !timezone, !todolist, !discord2, !discussion, !translate')
		await ctx.send('!slots, !gamble, !collect, !invest', '!so')
		# Help command
		await ctx.send('For more information on a command type !help <command>')

	# help command
	@commands.command(name='help')
	async def help_command(self, ctx: commands.Context, command: str):
		_logger.info(f'{ctx.author.name} is calling the help command and requesting help for {command}')
		# Help command
		await ctx.send(f'Help for command: {command}')
		if command == 'roomba':
			await ctx.send('The roomba command is used collect dustbunnies.')
		elif command == 'points':
			await ctx.send(
				'The points command is used to get the stats of all command. Format: !points optional <username>')
		elif command == 'brb':
			await ctx.send('The brb command is used to set a timer for when you will be back.')
		elif command == 'timer':
			await ctx.send('The timer command is used to set a timer. Format: !timer <type> <time in minutes>')
		elif command == 'lurk':
			await ctx.send('The lurk command is used to lurk in the chat.')
		elif command == 'suika':
			await ctx.send('The suika command is used to play the suika game.')
		elif command == 'timezone':
			await ctx.send('The timezone command is used to get the current time in Germany.')
		elif command == 'todolist':
			await ctx.send('The todolist command is used to add, list, or clear items from the to-do list.')
		elif command == 'discord2':
			await ctx.send('The discord command is used to get the discord link.')
		elif command == 'discussion':
			await ctx.send('The discussion command is used to get a discussion topic.')
		elif command == 'translate':
			await ctx.send('The translate command is used to translate text. Format: !translate <text>')
		elif command == 'slots':
			await ctx.send('The slots command is used to gamble points. Format: !slots <amount> or !slots all')
		elif command == 'gamble':
			await ctx.send('The gamble command is used to gamble points. Format: !gamble <amount> or !gamble all')
		elif command == 'collect':
			await ctx.send('The collect command is used to collect interest on investments.')
		elif command == 'invest':
			await ctx.send('The bank command is used to invest points. This is final Format: !invest <amount>')
		elif command == 'so':
			await ctx.send('The so command is used to give a shoutout. Format: !so <username>')
		else:
			await ctx.send('Command not found.')

	@commands.command(name='hug', aliases=('cuddle', 'snuggle'))
	async def hug_command(self, ctx: commands.Context, username: str = None):
		# List of funny hug messages
		hug_messages = [
			"squeezes @{username} like a teddy bear! 🧸",
			"gives @{username} the warmest bear hug! 🐻",
			"hugs @{username} so tightly that their worries vanish! 🌈",
			"wraps @{username} in a burrito of love! 🌯",
			"sends @{username} a virtual hug full of good vibes! 🌟",
			"hugs @{username} like it's their last hug on Earth! 🌍",
			"gives @{username} a hug so big, even gravity feels it! 🌌",
			"hugs @{username} and whispers, 'Everything's going to be okay.' 🥰",
			"hugs @{username} and doesn't let go for an awkwardly long time. 😳",
			"turns @{username} into a hug sandwich! 🥪",
			"hugs @{username} while humming a happy tune! 🎵",
			"hugs @{username} with the power of a thousand suns! ☀️",
			"gives @{username} a hug and a cookie! 🍪",
			"hugs @{username} so tightly that their soul gets cozy! ✨",
			"shares a cosmic hug with @{username}! 🚀",
			"gives @{username} the squishiest hug ever! 🫧",
			"hugs @{username} and sneaks a pat on the back! 🖐️",
			"throws @{username} into a hug tornado! 🌪️",
			"hugs @{username} like they're reuniting after 100 years! ⏳",
			"hugs @{username} while softly saying 'no takebacks!' 😜",
			"hugs @{username} and slips them a friendship bracelet. 🧶",
			"gives @{username} a magical hug with sparkles! ✨",
			"hugs @{username} and adds a sprinkle of love dust! 💖",
			"hugs @{username} while tap-dancing around! 🎩",
			"hugs @{username} and spins them in a circle! 🌀",
			"gives @{username} a hug so sweet it could melt chocolate! 🍫",
			"hugs @{username} and says, 'Tag, you're it!' 🏷️",
			"hugs @{username} like a koala on a eucalyptus tree! 🐨",
			"hugs @{username} with a big goofy smile! 😁",
			"gives @{username} the best hug in the multiverse! 🌠"
		]

		# Log the hug attempt
		_logger.info(f'{ctx.author.name} is hugging {username}')

		# Default message if no username is provided
		if not username:
			await ctx.send(f"@{ctx.author.name} is hugging the world! 🌍")
			return

		# Remove '@' if included and convert username to lowercase
		if '@' in username:
			username = username[1:]
		username = username.lower()

		# Select a random hug message
		hug_message = random.choice(hug_messages).format(username=username)

		# Send the hug message
		await ctx.send(f"@{ctx.author.name} {hug_message}")


bot = Bot()
bot.run()
