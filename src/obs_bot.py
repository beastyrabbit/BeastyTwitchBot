import os

from obsws_python import ReqClient
from twitchio.ext import commands, routines

from config.global_methods import get_discussion_topic_for_technology, translate_text, redis_client
from config.base_values import CHANNEL_NAME, setup_logger, get_valid_token
from objects.object_manager import UserManager, ObjectManager
import obsws_python as obs

_logger = setup_logger(__name__)

#TODO: DO STUFF

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

		# Define connection details
		host = "192.168.160.193"
		port = 4455
		password = os.getenv("OBS_PASSWORD")
		# Connect to OBS
		self.cl = obs.ReqClient(host=host, port=port, password=password, timeout=3)

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
		await self.get_channel(CHANNEL_NAME).send("I'm OBS God!")

	async def event_message(self, message):
		# Messages with echo set to True are messages sent by the bot...
		# For now we just want to ignore them...
		if message.echo:
			return
		# Since we have commands and are overriding the default `event_message`
		# We must let the bot know we want to handle and invoke our commands...
		await self.handle_commands(message)

	@commands.command(name='brb2')
	async def brb_command(self, ctx: commands.Context, time: str):
		_logger.info(f'User {ctx.author.name} is calling the brb command')
		scene_name = "Scene BRB"
		self.cl.set_current_program_scene(scene_name)
		_logger.info(f"Scene changed to: {scene_name}")

	@commands.command(name='esuika')
	async def esuika_command(self, ctx: commands.Context):
		_logger.info(f'User {ctx.author.name} is calling the esuika command')
		current_scene = self.cl.get_current_program_scene().current_program_scene_name
		scene_item_id = self.cl.get_scene_item_id(scene_name=current_scene, source_name="Suika Game Lite").scene_item_id
		_logger.debug(f"This is the current scene: {current_scene}")
		_logger.debug(f"This is the scene item id: {scene_item_id}")
		self.cl.set_scene_item_enabled(current_scene, scene_item_id, False)


bot = Bot()
bot.run()
