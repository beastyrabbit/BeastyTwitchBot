from datetime import datetime, timedelta
from enum import Enum

from .base_values import redis_client, setup_logger
from .user import User

_logger = setup_logger(__name__)


class BotList(Enum):
	admin = "admin"
	viewer = "viewer"
	gamble = "gamble"
	dustbunny = "dustbunny"
	obs = "obs"


class OfficialCommands(Enum):
	roomba = "roomba"
	gamble = "gamble"
	invest = "invest"
	fight = "fight"
	lurk = "lurk"
	help = "help"


class SettingsManager:
	def __init__(self):
		self._commands = {}  # Use a dictionary for faster lookup
		for command in OfficialCommands:
			if command == OfficialCommands.roomba:
				self._commands[command] = Clean()
			elif command == OfficialCommands.invest:
				self._commands[command] = Invest()
			else:
				self._commands[command] = Command(command)

	def getCommand(self, command: OfficialCommands):
		return self._commands.get(command)

	def check_user_not_in_timeout(self, user: User, command: OfficialCommands) -> bool:
		curr_command = self.getCommand(command)
		if curr_command:  # Check if the command exists
			return curr_command.check_user_not_in_timeout(user)
		return False  # return false if command doesnt exist (and in this way not allow it)


class Command:
	def __init__(self, type: OfficialCommands):
		self._type = type
		self._timeout_key = f"beastyrabbit:command:{type}"  # Store the key for this command

	@property
	def type(self):
		return self._type

	@property
	def timeout_in_seconds(self):
		value = redis_client.hget(self._timeout_key, "timeout_in_seconds")
		return int(value) if value is not None else 30

	def set_user_timeout(self, user: User):
		redis_client.hset(f'beastyrabbit:command:{self._type}:user:{user.username}', "timeout",
		                  datetime.utcnow().isoformat())

	def check_user_not_in_timeout(self, user: User) -> bool:
		timeout_user_key = f'beastyrabbit:command:{self._type}:user:{user.username}'
		if not redis_client.hexists(timeout_user_key, "timeout"):
			self.set_user_timeout(user)
			_logger.debug(f"User {user.username} has no timeout set. Setting one now.")
			return True
		last_timeout = datetime.fromisoformat(redis_client.hget(timeout_user_key, "timeout"))
		if datetime.utcnow() - last_timeout > timedelta(seconds=self.timeout_in_seconds):  # use dynamic timeout
			_logger.debug(f"User {user.username} timeout expired. Good to go again.")
			self.set_user_timeout(user)
			return True
		_logger.debug(f"User {user.username} is still in timeout.")  # slightly more informative message
		return False


class Clean(Command):
	def __init__(self):
		super().__init__(OfficialCommands.roomba)
		self._max_value_key = f'beastyrabbit:command:{self._type}'  # Store the key

	@property
	def current_max_value(self):
		value = redis_client.hget(self._max_value_key, 'max_value')
		return int(value) if value is not None else 1000

	@current_max_value.setter
	def current_max_value(self, value):
		redis_client.hset(self._max_value_key, 'max_value', value)


class Invest(Command):
	def __init__(self):
		super().__init__(OfficialCommands.invest)
		self._interest_rate_key = f"beastyrabbit:command:{self._type}"

	@property
	def daily_interest_rate(self):
		value = redis_client.hget(self._interest_rate_key, "interest_rate")
		return float(value) if value is not None else 0.02
