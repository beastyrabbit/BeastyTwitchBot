from typing import Dict

from config.global_methods import setup_logger
from config.base_values import redis_client
from objects.user import User

logger = setup_logger(__name__)


class UserManager:
	def __init__(self):
		self._users: Dict[str, User] = {}

	def get_all_users(self):
		all_users = redis_client.hgetall('beastyrabbit:users')
		return all_users

	def get_all_user_objects(self):
		all_users = self.get_all_users()
		user_objects = []
		for user in all_users:
			user_objects.append(self.get_user(user))
		return user_objects

	def check_user_exists(self, username: str) -> bool:
		username = username.lower()
		logger.debug(f'Checking user: {username} in {self._users}')
		for user in self._users:
			if user == username:
				return True
		return False

	def create_user(self, username) -> User:
		# create a user and store by username
		if username not in self._users:
			new_user: User = User(username)
			self._users[username] = new_user
			return new_user
		else:
			return self._users[username]

	def get_user(self, username) -> User:
		# create a user and store by username
		if username not in self._users:
			new_user: User = User(username)
			self._users[username] = new_user
		return self._users[username]

	def delete_user(self, username):
		self.check_user_exists(username)
		if username in self._users:
			logger.warning(f'Deleting user: {username}')
			self._users[username].delete_user()
			temp = self._users.pop(username, None)
			logger.debug(f'Deleted user: {temp} from {self._users}')


class ObjectManager:
	def __init__(self):
		self._user_manager = UserManager()

	@property
	def user_manager(self) -> UserManager:
		return self._user_manager


# Create a global manager instance
object_manager = ObjectManager()
