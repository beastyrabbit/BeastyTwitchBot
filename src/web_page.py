import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

from src.helperfunc.object_manager import object_manager

user_manager = object_manager.user_manager
# Streamlit Config
st.set_page_config(page_title="User Management", layout="wide")

# Sidebar Navigation
page = st.sidebar.radio("Navigation", ["User List", "Edit User"])

# 🌟 **1. User List Page**
if page == "User List":
	st.title("👥 User Management")
	st.write("Manage users directly from the table below:")

	# Prepare user data for the table
	data = pd.DataFrame([{
		"username": user.username,
		"clean_points_collected": user.clean_points_collected,
		"command_count": user.command_count,
		"timestamp_last_command": user.timestamp_last_command,
		"gambling_results": user.gambling_results,
		"gambling_input": user.gambling_input,
		"gambling_wins": user.gambling_wins,
		"gambling_losses": user.gambling_losses,
		"fight_requested_by": user.fight_requested_by,
		"fights_won": user.fights_won,
		"fights_lost": user.fights_lost,
		"points_invested": user.points_invested,
		"timestamp_investment": user.timestamp_investment,
		"points_collected_from_investment": user.points_collected_from_investment
	} for user in user_manager.get_all_user_objects()])

	# Configure AgGrid
	gb = GridOptionsBuilder.from_dataframe(data)
	gb.configure_default_column(editable=True, groupable=True)
	grid_options = gb.build()

	grid_response = AgGrid(
		data,
		gridOptions=grid_options,
		editable=True,
		height=400,
		key='user_table'
	)

	# Apply Changes
	if st.button("Save Changes"):
		updated_data = grid_response['data']
		for index, row in updated_data.iterrows():
			username = row['username']
			user = user_manager.get_user(username)
			if user:
				user.clean_points_collected = row['clean_points_collected']
				user.command_count = row['command_count']
				user.timestamp_last_command = row['timestamp_last_command']
				user.gambling_results = row['gambling_results']
				user.gambling_input = row['gambling_input']
				user.gambling_wins = row['gambling_wins']
				user.gambling_losses = row['gambling_losses']
				user.fight_requested_by = row['fight_requested_by']
				user.fights_won = row['fights_won']
				user.fights_lost = row['fights_lost']
				user.points_invested = row['points_invested']
				user.timestamp_investment = row['timestamp_investment']
				user.points_collected_from_investment = row['points_collected_from_investment']
		st.success("User data updated successfully!")
		st.experimental_rerun()

	# User Deletion
	delete_user = st.selectbox("Select User to Delete:", user_manager.get_all_users())
	if st.button("Delete Selected User"):
		user_manager.delete_user(delete_user)
		st.success(f"User '{delete_user}' deleted successfully!")
		st.experimental_rerun()

# ✍️ **2. Edit Individual User Page**
if page == "Edit User":
	st.title("✍️ Edit User Details")

	selected_user = st.selectbox("Select User to Edit:", user_manager.get_all_users())

	if selected_user:
		user = user_manager.get_user(selected_user)

		with st.form("edit_user_form"):
			clean_points_collected = st.number_input("Clean Points Collected", value=user.clean_points_collected)
			command_count = st.number_input("Command Count", value=user.command_count)
			timestamp_last_command = st.number_input("Timestamp Last Command", value=user.timestamp_last_command)
			gambling_results = st.number_input("Gambling Results", value=user.gambling_results)
			gambling_input = st.number_input("Gambling Input", value=user.gambling_input)
			gambling_wins = st.number_input("Gambling Wins", value=user.gambling_wins)
			gambling_losses = st.number_input("Gambling Losses", value=user.gambling_losses)
			fight_requested_by = st.text_input("Fight Requested By", value=user.fight_requested_by)
			fights_won = st.number_input("Fights Won", value=user.fights_won)
			fights_lost = st.number_input("Fights Lost", value=user.fights_lost)
			points_invested = st.number_input("Points Invested", value=user.points_invested)
			timestamp_investment = st.number_input("Timestamp Investment", value=user.timestamp_investment)
			points_collected_from_investment = st.number_input(
				"Points Collected from Investment", value=user.points_collected_from_investment
			)

			submitted = st.form_submit_button("Save Changes")
			if submitted:
				user.clean_points_collected = clean_points_collected
				user.command_count = command_count
				user.timestamp_last_command = timestamp_last_command
				user.gambling_results = gambling_results
				user.gambling_input = gambling_input
				user.gambling_wins = gambling_wins
				user.gambling_losses = gambling_losses
				user.fight_requested_by = fight_requested_by
				user.fights_won = fights_won
				user.fights_lost = fights_lost
				user.points_invested = points_invested
				user.timestamp_investment = timestamp_investment
				user.points_collected_from_investment = points_collected_from_investment

				st.success("User updated successfully!")
				st.experimental_rerun()
