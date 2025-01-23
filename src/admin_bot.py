from twitchio.ext import commands, routines

from src.helperfunc.base_values import redis_client
from src.helperfunc.global_methods import get_discussion_topic_for_technology, translate_text
from src.helperfunc.base_values import CHANNEL_NAME, setup_logger, get_valid_token
from helperfunc.object_manager import UserManager, ObjectManager

_logger = setup_logger(__name__)


class Bot(commands.Bot):
	def __init__(self):
		# Initialise our Bot with our access token, prefix and a list of channels to join on boot...
		# prefix can be a callable, which returns a list of strings or a string...
		# initial_channels can also be a callable which returns a list of strings...
		access_token = get_valid_token()
		self.access_token = access_token
		self.object_manager = ObjectManager
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
		self.hourly_check.start()
		await self.get_channel(CHANNEL_NAME).send("Admin online be careful!")

	async def event_message(self, message):
		# Messages with echo set to True are messages sent by the bot...
		# For now we just want to ignore them...
		if message.echo:
			return
		# Since we have commands and are overriding the default `event_message`
		# We must let the bot know we want to handle and invoke our commands...
		await self.handle_commands(message)

	@routines.routine(hours=1)
	async def hourly_check(self):
		# get message count from redis
		message_count = redis_client.hget('stream:global', 'messege_counter')
		message_count = int(message_count)
		_logger.debug(f'Current Message count for hourly message : {message_count}')
		if message_count > 20:
			# Send a message to the chat if count is higher than 20
			channel = self.get_channel(CHANNEL_NAME)
			if channel:
				# send mesaage to Follow and check out the discord and !suika
				await channel.send(
					'If you like the Content please consider following and check out the discord! 🐰🐻' 'Do you want to play Suikagame? Type !suika in chat 🍉🍉🍉' 'Get your shitty Doodle with some Carrot Charms!')

				# reset the message count
				redis_client.hset('stream:global', 'messege_counter', 0)
		else:
			# Optionally log this case for debugging
			_logger.info('Message count was below 20, no message sent.')

	# discord
	@commands.command(name='discord')
	async def discord_command(self, ctx: commands.Context):
		if not ctx.author.is_mod:
			return
		_logger.info(f'{ctx.author.name} is calling the discord command')
		await ctx.send('Join the discord server at https://discord.gg/dPdWbv8xrj')

	@commands.command(name='so')
	async def give_shoutout(self, ctx: commands.Context, username: str):
		_logger.info(f'{ctx.author.name} requested a shoutout for {username}')

		if not username:
			return

		# check if user is mod
		if not ctx.author.is_mod:
			return
		if username.startswith('@'):
			username = username[1:]
		username = username.lower()

		user = await self.fetch_users(names=[username])
		if not user:
			_logger.error(f'User {username} not found.')
			return

		user_id = user[0].id
		streams = await self.fetch_channels(broadcaster_ids=[user_id])

		if streams:
			stream = streams[0]
			game_name = stream.game_name
			title = stream.title
			# build twitch url for the user
			twitch_url = f'https://www.twitch.tv/{username}'
			# await ctx.send(f'You should check out {username} was last playing {game_name} with the title: {title}! 🐰🐻 at {twitch_url}')
			shoutout_message = f'You should check out {username} was last playing =>{game_name}<= with the title: {title}! 🐰🐻 at {twitch_url}'
			# real shoutout from twitch
			user = self.create_user('29319793', 'Beastyrabbit')
			await user.chat_announcement(token=self.access_token, moderator_id='1215902100', message=shoutout_message,
			                             color='purple')
			await user.shoutout(to_broadcaster_id=user_id, moderator_id='1215902100', token=self.access_token)

	# await ctx.send(f'/shoutout {username}')

	@commands.command(name='brb')
	async def brb_command(self, ctx: commands.Context, time: str):
		_logger.info(f'User {ctx.author.name} requested a brb command for {time} minutes.')
		if not ctx.author.is_mod:
			if not ctx.author.is_vip:
				await ctx.send('Only mods can use this command 🚨!')
				return
		# Brb command to set a timer and let the channel know you'll be right back...
		# We can store the amount of messages cleaned up in a database...
		if ctx.author.is_broadcaster:
			await ctx.send(
				f'I’ll be back in {time} minutes 🐰🐻! Meanwhile, have fun playing Suika 🍉🍉🍉 by typing `!join`.')
			await ctx.send(
				' You can play Suika by typing !join. When its your turn put 0-100 in chat. If you want to leave the game type !leave. 🍉🍉🍉')
		else:
			await ctx.send(f'@{ctx.author.name} I’ll be back in {time} minutes 🐰🐻!')

	# todolist add / list / clear
	@commands.command(name='todolist', aliases=('todo', 'list'))
	async def todolist_command(self, ctx: commands.Context, action: str, *args):
		_logger.info(
			f'User {ctx.author.name} requested a to-do list command with action: {action} and arguments: {args}')
		# Define the Redis key for the to-do list
		todo_key = 'todolist'

		# Check the action requested by the user
		if action == 'add':
			# Add a new item to the to-do list
			todo_item = ' '.join(args)
			redis_client.rpush(todo_key, todo_item)
			await ctx.send(f'Added to-do item: {todo_item}')
		elif action == 'list':
			# Retrieve the current to-do list
			todo_list = redis_client.lrange(todo_key, 0, -1)
			if not todo_list:
				await ctx.send('The to-do list is empty.')
			else:
				# Send each item in the to-do list to the chat
				for index, item in enumerate(todo_list, start=1):
					await ctx.send(f'{index}. {item}')
		elif action == 'clear':
			# Clear all items from the to-do list
			redis_client.delete(todo_key)
			await ctx.send('Cleared all items from the to-do list.')
		else:
			# Inform the user about the available actions
			await ctx.send('Please specify an action: add, list, or clear.')

	# discussion / aitopic
	@commands.command(name='discussion', aliases=('aitopic'))
	async def discussion_command(self, ctx: commands.Context):
		_logger.info(f'User {ctx.author.name} requested a discussion topic.')
		message = get_discussion_topic_for_technology()
		_logger.debug(f'New Topic was generated: {message}')
		await ctx.send('New Topic was generated! 🤖 ')
		# split trenslation for it is long then 500 characters
		if len(message) > 500:
			for i in range(0, len(message), 500):
				await ctx.send(f'Discussion Topic: {message[i:i + 500]}')
		else:
			await ctx.send(f'Discussion Topic: {message}')

	# translate
	@commands.command(name='translate', aliases=('tr', 'trans'))
	async def translate_command(self, ctx: commands.Context, *, text: str):
		_logger.info(f'User {ctx.author.name} requested a translation for text: {text}')
		translation = translate_text(text)
		# get_text_to_spech(translation, output_name='translation')
		# split trenslation for it is long then 500 characters
		if len(translation) > 500:
			for i in range(0, len(translation), 500):
				await ctx.send(f'Translation: {translation[i:i + 500]}')
		else:
			await ctx.send(f'Translation: {translation}')


bot = Bot()
bot.run()
