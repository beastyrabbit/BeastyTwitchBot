from flask import Flask, jsonify, render_template, request

from config.global_methods import setup_logger

app = Flask(__name__)
logger = setup_logger(__name__)
object_manager = None


# ---------- API Routes ----------


@app.route('/user/<username>', methods=['GET'])
def get_user_data(username):
	"""Retrieve user data."""
	user = object_manager.user_manager.get_user(username)
	user_data = {
		'clean_points_collected': user.clean_points_collected,
		'command_count': user.command_count,
		'timestamp_last_command': user.timestamp_last_command,
		'gambling_results': user.gambling_results,
		'gambling_input': user.gambling_input,
		'gambling_wins': user.gambling_wins,
		'gambling_losses': user.gambling_losses,
		'fight_requested_by': user.fight_requested_by,
		'fights_won': user.fights_won,
		'fights_lost': user.fights_lost,
		'points_invested': user.points_invested,
		'timestamp_investment': user.timestamp_investment,
		'points_collected_from_investment': user.points_collected_from_investment,
	}
	return jsonify(user_data)


@app.route('/user/<username>', methods=['POST'])
def update_user_data(username):
	"""Update user data."""
	user = object_manager.user_manager.get_user(username)
	data = request.json
	# logger.debug(f'Updating user {username} with data: {data}')

	allowed_fields = [
		'clean_points_collected',
		'command_count',
		'timestamp_last_command',
		'gambling_results',
		'gambling_input',
		'gambling_wins',
		'gambling_losses',
		'fight_requested_by',
		'fights_won',
		'fights_lost',
		'points_invested',
		'timestamp_investment',
		'points_collected_from_investment',
	]
	for key, value in data.items():
		if key in allowed_fields:
			if value != '':
				logger.debug(f'Updating {key} for {username} to {value}')
				user = object_manager.user_manager.get_user(username)
				user.__setattr__(key, value)

	return jsonify({'message': f'User {username} updated successfully'})


@app.route('/users', methods=['GET'])
def list_users():
	"""List all users."""
	logger.debug(f'object_manager: {object_manager}')
	all_users = object_manager.user_manager.get_all_users()
	# logger.debug(f'loaded all users for Admin Interface: {all_users}')
	return jsonify(list(all_users))


# ---------- Web Interface ----------


@app.route('/')
def index():
	"""Render the main webpage."""
	global object_manager
	object_manager = app.config.get('object_manager')
	return render_template('index.html')


@app.route('/user/<username>/edit')
def edit_user(username):
	"""Render the user edit page."""
	user = object_manager.user_manager.get_user(username)
	return render_template('edit_user.html', username=username, user=user)


@app.route('/user/<username>', methods=['DELETE'])
def delete_user(username):
	"""Render the user delete page."""
	object_manager.user_manager.delete_user(username)
	return jsonify({'message': f'User {username} deleted successfully'})


if __name__ == '__main__':
	app.run(host='192.168.50.186', port=5000, debug=True)
