from datetime import datetime

from twitchio.ext import commands
import os, sys
from config.global_methods import calculate_interest, do_the_cleaning_command, generate_rnd_amount_to_steal
from config.base_values import CHANNEL_NAME, setup_logger, get_valid_token
from objects.object_manager import ObjectManager, UserManager

_logger = setup_logger(__name__)

sys.path.append(os.path.dirname(__file__))


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
		await self.get_channel(CHANNEL_NAME).send("Dustbunny Bot is online!")

	async def event_message(self, message):
		# Messages with echo set to True are messages sent by the bot...
		# For now we just want to ignore them...
		if message.echo:
			return
		# Since we have commands and are overriding the default `event_message`
		# We must let the bot know we want to handle and invoke our commands...
		await self.handle_commands(message)

	@commands.command(name='giveall')
	async def giveall_command(self, ctx: commands.Context, amount: str):
		_logger.info(f'{ctx.author.name} is giving {amount} points to everyone')
		amount = int(amount)
		if ctx.author.is_mod:
			# dont remove only add
			all_users = self.user_manager.get_all_user_objects()
			for user in all_users:
				user.clean_points_collected = user.clean_points_collected + amount
			return

	@commands.command(name='give')
	async def give_command(self, ctx: commands.Context, username: str, amount: str):
		_logger.info(f'{ctx.author.name} is giving {amount} points to {username}')
		# if usname is @ remove it
		amount = int(amount)
		if '@' in username:
			username = username[1:]
		username = username.lower()
		if ctx.author.is_mod:
			# dont remove only add
			self.user_manager.get_user(username).clean_points_collected += amount
			return
		# no more so check if user has enough points
		if self.user_manager.get_user(ctx.author.name).clean_points_collected < amount:
			await ctx.send(f'You do not have enough points to give {amount} points! 😢')
			return
		# remove the amount from the user
		self.user_manager.get_user(ctx.author.name).clean_points_collected -= amount
		# check if user exists
		self.user_manager.get_user(username).clean_points_collected += amount
		await ctx.send(f'{ctx.author.name} gave {amount} Dustbunnies to {username}! 🐰🐻')

	@commands.command(name='steal')
	async def steal_command(self, ctx: commands.Context, username: str):
		_logger.info(f'{ctx.author.name} is stealing from {username}')
		# if usname is @ remove it
		if '@' in username:
			username = username[1:]
		username = username.lower()
		# stealing should get exponentially harder up to 10x the max value
		# you cant steal from the bank but everything till 0 from the inventory
		stolen_amount = generate_rnd_amount_to_steal()
		await ctx.send(
			f'{ctx.author.name} stole {stolen_amount} Dustbunnies from {username}! 🐰🐻 But lucky its just a test for now!')

	@commands.command(name='collect', aliases=('interest'))
	async def collect_command(self, ctx: commands.Context):
		_logger.info(f'{ctx.author.name} is collecting interest')
		user = self.user_manager.get_user(ctx.author.name)
		interest_collected = calculate_interest(user)
		if interest_collected > 0:
			user.clean_points_collected += interest_collected
			await ctx.send(f'{ctx.author.name} collected {interest_collected} Dustbunnies! 🐰🐻')
		else:
			await ctx.send(f'{ctx.author.name} you do not have any Dustbunnies to collect! Maybe invest some more 😢')

	@commands.command(name='invest', aliases=('investment', 'bank'))
	async def invest_command(self, ctx: commands.Context, amount: str):
		_logger.info(f'{ctx.author.name} is investing {amount} points')
		user = self.user_manager.get_user(ctx.author.name)
		amount = int(amount)
		# investing removes the points from the user and never gives them back
		# but with the command intrest the user can get points back
		# till a minimum value that was put in by the user

		interest_collected = calculate_interest(user)
		if interest_collected > 0:
			await ctx.send(f'{ctx.author.name} collected {interest_collected} Dustbunnies from their investment! 🐰🐻')
			user.clean_points_collected += interest_collected

		# check if user has enough points
		if int(user.clean_points_collected) < amount:
			await ctx.send(f'You do not have enough points to invest {amount} points! 😢')
			return

		# remove the amount from the user
		user.clean_points_collected -= amount
		# check if user has invested before
		user.points_invested += amount
		# store timestamp
		current_time = datetime.utcnow().isoformat()
		user.timestamp_investment = current_time
		await ctx.send(f'{ctx.author.name} invested {amount} Dustbunnies! 🐰🐻')

	@commands.command(name='roomba', aliases=('clean', 'vacuum'))
	async def roomba_command(self, ctx: commands.Context):
		_logger.info(f'{ctx.author.name} is cleaning up the channel')
		user = self.user_manager.get_user(ctx.author.name)
		# Roomba command to clean up the channel...
		# We can store the amount of messages cleaned up in a database...
		random_value, max_value_hit = do_the_cleaning_command(user)
		if max_value_hit:
			# Congratulate the user for hitting the max value
			await ctx.send(f'{ctx.author.name} hit the max value! 🐰🐻')
			await ctx.send(f'@Beastyrabbit Max Clean Value just was increased by {ctx.author.name}.! 🐰🐻')

		elif random_value == 69:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Nice! 😎')

		elif random_value == 420:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Blazing! 😎')

		elif random_value == 666:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Hail 😈!')

		elif random_value == 1337:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Elite! 🤖')

		elif random_value == 80085:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Boobs! 🍑')

		elif random_value == 8008:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Boob! 🍑')

		elif random_value == 8008135:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Boobies! 🍑🍑')

		elif random_value == 619:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! San Diego! 🌴')

		elif random_value == 42:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! The Answer! 🤖')

		elif random_value == 404:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Not Found! 🤖')

		elif random_value == 9001:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Over 9000! 🤖')

		# 007
		elif random_value == 7:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Bond! 🤵')

		elif random_value == 911:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Emergency! 🚨')

		# cash now
		elif random_value == 1800:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰🐻! Cash Now! 💰')

		elif random_value > 0:
			# Username cleaned up random_value messages...
			await ctx.send(f'{ctx.author.name} cleaned up {random_value} Dustbunnies 🐰!')


bot = Bot()
bot.run()
