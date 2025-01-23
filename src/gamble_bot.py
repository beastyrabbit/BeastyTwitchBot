import random
from typing import TYPE_CHECKING

from twitchio.ext import commands

from src.helperfunc.global_methods import global_settings_Manager
from src.helperfunc.base_values import CHANNEL_NAME, get_valid_token, redis_client, setup_logger
from helperfunc.setting import OfficialCommands

if TYPE_CHECKING:
	from helperfunc.object_manager import UserManager, ObjectManager

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
		await self.get_channel(CHANNEL_NAME).send("Get ready to Gamble!!")

	async def event_message(self, message):
		# Messages with echo set to True are messages sent by the bot...
		# For now we just want to ignore them...
		if message.echo:
			return
		# Since we have commands and are overriding the default `event_message`
		# We must let the bot know we want to handle and invoke our commands...
		await self.handle_commands(message)

	@commands.command(name='slots')
	async def slots_command(self, ctx: commands.Context, amount: int):
		_logger.info(f'{ctx.author.name} is slots gambling {amount} points')
		user = self.user_manager.get_user(ctx.author.name)
		if not global_settings_Manager.check_user_not_in_timeout(user, OfficialCommands.gamble):
			# _logger.debug(f'{ctx.author.name} is in timeout for slots')
			return
		# Gambling command to gamble some points...
		# We can store the amount of points gambled in a database...
		# get dustbunnies for user
		if amount == 'all':
			amount = user.clean_points_collected
		if user.clean_points_collected < amount:
			await ctx.send(f'You do not have enough points to gamble {amount} points! 😢')
			return

		# we will store the amount of points gambled in a database
		user.gambling_input += amount
		user.clean_points_collected -= amount

		# do the gambling
		# we have 3 independent slots with 10 outcomes 7 fruits and 2 price icons 1 jackpot
		# if all 3 slots are the same fruit you win 3x the amount
		# if all 3 slots are the same price icon you win 10x the amount
		# if all 3 slots are the same jackpot you win 100x the amount

		array_for_slors = ['🍇', '🍒', '🍋', '🍊', '🍎', '🍓', '🍌', '💰', '💎', '🎰']
		slot1 = random.choice(array_for_slors)
		slot2 = random.choice(array_for_slors)
		slot3 = random.choice(array_for_slors)

		# tell the user the slot results
		await ctx.send(f'{ctx.author.name} Slot Results: {slot1} {slot2} {slot3}')
		gamble_result = 0
		if slot1 == slot2 == slot3:
			if slot1 == '🎰':
				gamble_result = amount * 100
			elif slot1 in ['💰', '💎']:
				gamble_result = amount * 10
			else:
				gamble_result = amount * 3

		# we will store the amount of points won or lost in a database
		# remove the amount from the user

		if gamble_result > 0:
			user.gambling_results += gamble_result
			user.clean_points_collected += gamble_result
			user.gambling_wins += gamble_result
		else:
			user.gambling_losses += amount
			user.gambling_results -= amount

		if gamble_result > 0:
			await ctx.send(f'You won {gamble_result} Dustbunnies! 🎉 All Dustbunnies are happy! 🐰🐻')
		else:
			await ctx.send(f'You lost {amount} Dustbunnies! 😢 Sad Dustbunnies! 🐰🐻')

	@commands.command(name='gamble', aliases=('bet', 'gambling'))
	async def gamble_command(self, ctx: commands.Context, amount: int):
		user = self.user_manager.get_user(ctx.author.name)
		if global_settings_Manager.check_user_not_in_timeout(user, OfficialCommands.gamble):
			_logger.debug(f'{ctx.author.name} is in timeout for gambling')
			return
		# Gambling command to gamble some points...
		# We can store the amount of points gambled in a database...
		# get dustbunnies for user
		# print(f'{ctx.author.name} is gambling {amount} points')
		if amount == 'all':
			amount = user.clean_points_collected
		if user.clean_points_collected < amount:
			await ctx.send(f'You do not have enough points to gamble {amount} points! 😢')
			return

		# we will store the amount of points gambled in a database
		user.gambling_input += amount

		# do the gambling
		gamble_result = random.choice([True, False])
		# print(f'gamble result: {gamble_result}')

		# we will store the amount of points won or lost in a database
		if gamble_result:
			user.gambling_results += amount
			user.clean_points_collected += amount
			user.gambling_wins += amount
		else:
			user.gambling_losses += amount
			user.gambling_results -= amount
			user.clean_points_collected -= amount

		if gamble_result:
			await ctx.send(f'You won {amount} Dustbunnies! 🎉 🐰🐻')
		else:
			await ctx.send(f'You lost {amount} Dustbunnies! 😢 🐰🐻')


# Blackjack game
# start a round when somebody want to play
# let anybody join for 60 sec
# start the game and deal card to the player and the dealer
# wait 60 sec for the player to decide to hit or stand or double down or split
# if player hits deal another card
# if all players are done do dealer logic
# commands: blackjack join, blackjack hit, blackjack stand, blackjack double, blackjack split


@commands.command(name='blackjack', aliases=('bj'))
async def blackjack_command(self, ctx: commands.Context, action: str, *args):
	_logger.info(f'User {ctx.author.name} requested a blackjack command with action: {action} and arguments: {args}')
	# Define the Redis key for the blackjack game
	blackjack_key = 'chat_command:clean:blackjack'
	# Check the action requested by the user
	if action == 'join':
		# Add a new player to the blackjack game
		redis_client.sadd(blackjack_key, ctx.author.name)
		await ctx.send(f'@{ctx.author.name} joined the Blackjack game!')
	elif action == 'hit':
		# Deal a new card to the player
		await ctx.send(f'@{ctx.author.name} hit!')
	elif action == 'stand':
		# Player stands
		await ctx.send(f'@{ctx.author.name} stands!')
	elif action == 'double':
		# Player doubles down
		await ctx.send(f'@{ctx.author.name} doubles down!')
	elif action == 'split':
		# Player splits their hand
		await ctx.send(f'@{ctx.author.name} splits!')
	else:
		# Inform the user about the available actions
		await ctx.send('Please specify an action: join, hit, stand, double, or split.')


bot = Bot()
bot.run()
