from config.base_values import setup_logger, redis_client

_logger = setup_logger(__name__)

USER_FIELDS = {
	'clean_points_collected': 0,
	'clean_max_hit_counter': 0,
	'command_count': 0,
	'timestamp_last_command': '',
	'gambling_results': 0,
	'gambling_input': 0,
	'gambling_wins': 0,
	'gambling_losses': 0,
	'fight_requested_by': '',
	'fights_won': 0,
	'fights_lost': 0,
	'points_invested': 0,
	'timestamp_investment': '',
	'points_collected_from_investment': 0,
	'lurk_counter': 0,
	'global_chats_send': 0
}


class User:
	def __init__(self, username):
		_logger.debug(f"Setting up user: {username}")
		self._username = username
		self._user_key = f'beastyrabbit:user:{self._username}'
		self._initialize_user()

	def _initialize_user(self):
		if redis_client.hexists('beastyrabbit:users', self._username) != 1:
			redis_client.hset('beastyrabbit:users', self._username, 1)
			for field, default_value in USER_FIELDS.items():
				redis_client.hset(self._user_key, field, default_value)

	@property
	def username(self):
		return self._username

	@property
	def clean_points_collected(self):
		value = redis_client.hget(self._user_key, 'clean_points_collected')
		return int(value) if value is not None else 0

	@clean_points_collected.setter
	def clean_points_collected(self, value):
		redis_client.hset(self._user_key, 'clean_points_collected', value)

	@property
	def clean_max_hit_counter(self):
		value = redis_client.hget(self._user_key, 'clean_max_hit_counter')
		return int(value) if value is not None else 0

	@clean_max_hit_counter.setter
	def clean_max_hit_counter(self, value):
		redis_client.hset(self._user_key, 'clean_max_hit_counter', value)

	@property
	def command_count(self):
		value = redis_client.hget(self._user_key, 'command_count')
		return int(value) if value is not None else 0

	@command_count.setter
	def command_count(self, value):
		redis_client.hset(self._user_key, 'command_count', value)

	@property
	def timestamp_last_command(self):
		return redis_client.hget(self._user_key, 'timestamp_last_command')

	@timestamp_last_command.setter
	def timestamp_last_command(self, value):
		redis_client.hset(self._user_key, 'timestamp_last_command', value)

	@property
	def gambling_results(self):
		value = redis_client.hget(self._user_key, 'gambling_results')
		return int(value) if value is not None else 0

	@gambling_results.setter
	def gambling_results(self, value):
		redis_client.hset(self._user_key, 'gambling_results', value)

	@property
	def gambling_input(self):
		value = redis_client.hget(self._user_key, 'gambling_input')
		return int(value) if value is not None else 0

	@gambling_input.setter
	def gambling_input(self, value):
		redis_client.hset(self._user_key, 'gambling_input', value)

	@property
	def gambling_wins(self):
		value = redis_client.hget(self._user_key, 'gambling_wins')
		return int(value) if value is not None else 0

	@gambling_wins.setter
	def gambling_wins(self, value):
		redis_client.hset(self._user_key, 'gambling_wins', value)

	@property
	def gambling_losses(self):
		value = redis_client.hget(self._user_key, 'gambling_losses')
		return int(value) if value is not None else 0

	@gambling_losses.setter
	def gambling_losses(self, value):
		redis_client.hset(self._user_key, 'gambling_losses', value)

	@property
	def fight_requested_by(self) -> str or None:
		return redis_client.hget(self._user_key, 'fight_requested_by')

	@fight_requested_by.setter
	def fight_requested_by(self, value: str or None = None):
		redis_client.hset(self._user_key, 'fight_requested_by', value)

	def clear_fight_requested_by(self):
		redis_client.hset(self._user_key, 'fight_requested_by', '')

	@property
	def fights_won(self):
		value = redis_client.hget(self._user_key, 'fights_won')
		return int(value) if value is not None else 0

	@fights_won.setter
	def fights_won(self, value):
		redis_client.hset(self._user_key, 'fights_won', value)

	@property
	def fights_lost(self):
		value = redis_client.hget(self._user_key, 'fights_lost')
		return int(value) if value is not None else 0

	@fights_lost.setter
	def fights_lost(self, value):
		redis_client.hset(self._user_key, 'fights_lost', value)

	@property
	def points_invested(self):
		value = redis_client.hget(self._user_key, 'points_invested')
		return int(value) if value is not None else 0

	@points_invested.setter
	def points_invested(self, value):
		redis_client.hset(self._user_key, 'points_invested', value)

	@property
	def timestamp_investment(self):
		return redis_client.hget(self._user_key, 'timestamp_investment')

	@timestamp_investment.setter
	def timestamp_investment(self, value):
		redis_client.hset(self._user_key, 'timestamp_investment', value)

	@property
	def points_collected_from_investment(self):
		value = redis_client.hget(self._user_key, 'points_collected_from_investment')
		return int(value) if value is not None else 0

	@points_collected_from_investment.setter
	def points_collected_from_investment(self, value):
		redis_client.hset(self._user_key, 'points_collected_from_investment', value)

	@property
	def lurk_counter(self):
		value = redis_client.hget(self._user_key, 'lurk_counter')
		return int(value) if value is not None else 0

	@lurk_counter.setter
	def lurk_counter(self, value):
		redis_client.hset(self._user_key, 'lurk_counter', value)

	@property
	def global_chats_send(self):
		value = redis_client.hget(self._user_key, 'global_chats_send')
		return int(value) if value is not None else 0

	@global_chats_send.setter
	def global_chats_send(self, value):
		redis_client.hset(self._user_key, 'global_chats_send', value)

	def get_gambling_total_played(self):
		return self.gambling_wins + self.gambling_losses

	def delete_user(self):
		redis_client.hdel('beastyrabbit:users', self.username)
		redis_client.delete(self._user_key)
