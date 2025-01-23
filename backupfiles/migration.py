from config.base_values import redis_client
from objects.object_manager import object_manager

user_manager = object_manager.user_manager

# loop over all clean_values and move them to the user

all_users = redis_client.hkeys('chat_command:clean:clean_values')
for user in all_users:
	print('-----------------')
	print(f'cleaned {user} with {user_manager.get_user(user).clean_points_collected} points') or 0
	user_manager.get_user(user).clean_points_collected = redis_client.hget('chat_command:clean:clean_values', user) or 0
	user_manager.get_user(user).command_count = redis_client.hget('chat_command:clean:command_count', user) or 0
	user_manager.get_user(user).timestamp_last_command = redis_client.hget('chat_command:clean:timestamps', user) or 0
	user_manager.get_user(user).gambling_results = redis_client.hget('chat_command:clean:gamble_results', user) or 0
	user_manager.get_user(user).gambling_input = redis_client.hget('chat_command:clean:gambled', user) or 0
	# user_manager.get_user(user).gambling_wins = redis_client.hget('chat_command:clean:gambling_wins', user)
	# user_manager.get_user(user).gambling_losses = redis_client.hget('chat_command:clean:gambling_losses', user)
	# user_manager.get_user(user).fight_requested_by = redis_client.hget('chat_command:fight:fight_requests', user)
	user_manager.get_user(user).fights_won = redis_client.hget('chat_command:fight:fight_results', user) or 0
	# user_manager.get_user(user).fights_lost = redis_client.hget('chat_command:clean:fights_lost', user)
	user_manager.get_user(user).points_invested = redis_client.hget('chat_command:investment:value_stored', user) or 0
	user_manager.get_user(user).timestamp_investment = redis_client.hget('chat_command:investment:timestamps',
	                                                                     user) or 0
	user_manager.get_user(user).points_collected_from_investment = redis_client.hget(
		'chat_command:investment:interest_collected', user) or 0
	user_manager.get_user(user).lurk_counter = redis_client.hget('chat_command:lurk:command_count', user) or 0
	# user_manager.get_user(user).global_chats_send = redis_client.hget('chat_command:clean:global_chats_send', user)
	print(f'cleaned {user} with {user_manager.get_user(user).clean_points_collected} points')
	print(f'cleaned {user} with {user_manager.get_user(user).command_count} commands')
	print(f'cleaned {user} with {user_manager.get_user(user).timestamp_last_command} timestamp_last_command')
	print(f'cleaned {user} with {user_manager.get_user(user).gambling_results} gambling_results')
	print(f'cleaned {user} with {user_manager.get_user(user).gambling_input} gambling_input')
	print(f'cleaned {user} with {user_manager.get_user(user).gambling_wins} gambling_wins')
	print(f'cleaned {user} with {user_manager.get_user(user).gambling_losses} gambling_losses')
	print(f'cleaned {user} with {user_manager.get_user(user).fight_requested_by} fight_requested_by')
	print(f'cleaned {user} with {user_manager.get_user(user).fights_won} fights_won')
	print(f'cleaned {user} with {user_manager.get_user(user).fights_lost} fights_lost')
	print(f'cleaned {user} with {user_manager.get_user(user).points_invested} points_invested')
	print(f'cleaned {user} with {user_manager.get_user(user).timestamp_investment} timestamp_investment')
	print(
		f'cleaned {user} with {user_manager.get_user(user).points_collected_from_investment} points_collected_from_investment')
	print(f'cleaned {user} with {user_manager.get_user(user).lurk_counter} lurk_counter')
	print(f'cleaned {user} with {user_manager.get_user(user).global_chats_send} global_chats_send')
	print('-----------------')
