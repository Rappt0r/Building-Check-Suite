from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.app import App
import csv
import os
import logging
import json
import glob
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration constants
TOOLTIP_TEXTS = {
    "new_check": "Start a new building check.",
    "resume_check": "Resume the last saved building check.",
    "navigation_back": "Go back to the previous screen.",
    "navigation_home": "Return to the main menu."
}

DEFAULT_CSV_FILENAME = "current_state.csv"
FLOORS_FILE = "floors.json"

# Load floors data
def load_floors_data():
    try:
        with open(FLOORS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"{FLOORS_FILE} not found.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding {FLOORS_FILE}: {e}")
        return {}

floors = load_floors_data()

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'

        self.add_widget(Label(text='IESLH Building Check', font_size=32))

        new_check_btn = self.create_button('New Check', self.new_check, TOOLTIP_TEXTS["new_check"], size_hint=(1, 0.2))
        resume_btn = self.create_button('Resume Check', self.resume_check, TOOLTIP_TEXTS["resume_check"], size_hint=(1, 0.2))

        self.add_widget(new_check_btn)
        self.add_widget(resume_btn)

        self.current_floor = 1
        self.initialize_room_status()

    def create_button(self, text, callback, tooltip_text, **kwargs):
        button = Button(text=text, **kwargs)
        button.bind(on_press=callback)
        # Tooltip can be added here (in full UI frameworks like Qt, Kivy lacks built-in tooltips)
        return button

    def initialize_room_status(self):
        self.room_status = {}
        for floor, rooms in floors.items():
            for room, details in rooms.items():
                self.room_status[room] = {
                    item.lower(): [{'status': '', 'notes': ''} for _ in range(count)] for item, count in details.items()
                }

    def new_check(self, instance):
        current_date = datetime.now().strftime('%Y-%m-%d')
        self.csv_file = f'check_results_{current_date}.csv'

        try:
            # Create a new file and write the headers
            with open(self.csv_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Room', 'Item', 'Index', 'Status', 'Notes'])  # Write the header row
            logging.info(f"New check file created: {self.csv_file}")
        except Exception as e:
            logging.error(f"Error creating new check file: {e}")

        # Remove any previous state
        if os.path.exists(DEFAULT_CSV_FILENAME):
            os.remove(DEFAULT_CSV_FILENAME)

        self.initialize_room_status()
        self.floor_selection()

    def resume_check(self, instance):
        csv_files = glob.glob('check_results_*.csv')
        logging.debug(f"Files found: {csv_files}")  # Log the files found
        if not csv_files:
            self.show_popup('Error', 'No previous check found. Ensure check files exist in the current directory.')
            return

        self.csv_file = max(csv_files, key=os.path.getmtime)  # Get the most recent file
        logging.info(f"Resuming from file: {self.csv_file}")
        
        self.load_previous_check()
        self.load_current_state()
        self.floor_selection()

    def show_popup(self, title, content):
        if isinstance(content, str):
            content = Label(text=content)
        self.popup = Popup(title=title, content=content, size_hint=(0.8, 0.8))
        self.popup.open()

    def load_previous_check(self):
        self.initialize_room_status()  # Reset room status
        try:
            logging.info(f"Loading data from {self.csv_file}")
            with open(self.csv_file, 'r') as file:
                reader = csv.reader(file)
                header = next(reader, None)  # Skip header
                logging.debug(f"File header: {header}")
                if not header or len(header) < 5:
                    logging.error(f"Invalid header in {self.csv_file}: {header}")
                    return

                for row in reader:
                    logging.debug(f"Processing row: {row}")
                    if len(row) >= 5:
                        try:
                            room = row[0]
                            item_type = row[1].lower()
                            item_index = int(row[2])
                            status = row[3]
                            notes = row[4]

                            if room in self.room_status and item_type in self.room_status[room]:
                                self.room_status[room][item_type][item_index] = {'status': status, 'notes': notes}
                                logging.info(f"Loaded status: Room {room}, {item_type.capitalize()} {item_index + 1} - {status}, Notes: {notes}")
                            else:
                                logging.warning(f"Room {room} or item {item_type} not found in configuration.")
                        except ValueError as e:
                            logging.error(f"Skipping invalid row in file: {row} | Error: {e}")
                    else:
                        logging.warning(f"Incomplete row: {row}")
        except Exception as e:
            logging.error(f"Error loading previous check file: {e}")

    def load_current_state(self):
        if not os.path.exists(DEFAULT_CSV_FILENAME):
            logging.warning("Current state file not found.")
            return

        try:
            with open(DEFAULT_CSV_FILENAME, 'r') as file:
                reader = csv.reader(file)
                header = next(reader, None)  # Skip header

                if not header or len(header) < 5:
                    logging.error(f"Invalid header in {DEFAULT_CSV_FILENAME}: {header}")
                    return

                for row in reader:
                    if len(row) != 5:
                        logging.warning(f"Skipping invalid row in current state: {row}")
                        continue

                    try:
                        room = row[0]
                        item = row[1]
                        index = int(row[2])
                        status = row[3]
                        notes = row[4]

                        if room in self.room_status and item in self.room_status[room]:
                            self.room_status[room][item][index] = {'status': status, 'notes': notes}
                            logging.info(f"Loaded status for Room {room}, {item.capitalize()} {index + 1}: {status}, Notes: {notes}")
                        else:
                            logging.warning(f"Room {room} or item {item} not found in the current configuration.")
                    except ValueError as e:
                        logging.error(f"ValueError while processing row: {row} | Error: {e}")

        except FileNotFoundError:
            logging.warning(f"File {DEFAULT_CSV_FILENAME} not found.")
        except Exception as e:
            logging.error(f"Error loading current state: {e}")

    def floor_selection(self):
        floor_selection = BoxLayout(orientation='vertical')
        self.add_navigation(floor_selection, 'Select Floor')

        for floor in floors:
            btn = Button(text=f'Floor {floor}')
            btn.bind(on_press=lambda x, floor=floor: self.show_room_check(floor))
            floor_selection.add_widget(btn)

        self.show_popup_content('Select Floor', floor_selection)

    def show_popup_content(self, title, content):
        self.popup = Popup(title=title, content=content, size_hint=(0.8, 0.8))
        self.popup.open()

    def add_navigation(self, layout, title):
        nav_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp')
        back_button = self.create_button('Back', self.go_back, TOOLTIP_TEXTS["navigation_back"], size_hint_x=None, width='50dp')
        home_button = self.create_button('Home', self.go_home, TOOLTIP_TEXTS["navigation_home"], size_hint_x=None, width='50dp')
        title_label = Label(text=title)
        
        nav_layout.add_widget(back_button)
        nav_layout.add_widget(title_label)
        nav_layout.add_widget(home_button)
        layout.add_widget(nav_layout)

    def go_back(self, instance):
        # Clear the current screen and show the floor selection screen
        self.clear_widgets()
        self.floor_selection()

    def go_home(self, instance):
        logging.info("Navigating back to the home screen.")
        self.clear_widgets()
        self.add_widget(MainScreen())

    def show_room_check(self, floor):
        self.current_floor = floor
        content = BoxLayout(orientation='vertical')
        self.add_navigation(content, f'Check Floor {floor}')

        # Create a scrollable view for room buttons
        scroll_view = ScrollView(size_hint=(1, 1))

        # Layout to hold the room buttons inside the scroll view
        room_buttons = BoxLayout(orientation='vertical', size_hint_y=None)
        room_buttons.bind(minimum_height=room_buttons.setter('height'))

        for room in floors[floor]:
            # Check room completion status
            all_checked = all(
                item['status'] for item_list in self.room_status[room].values() for item in item_list
            )
            partially_checked = any(
                item['status'] for item_list in self.room_status[room].values() for item in item_list
            )

            # Set status text
            if all_checked:
                status_text = f"Room {room}: Fully Checked"
            elif partially_checked:
                status_text = f"Room {room}: Partially Checked"
            else:
                status_text = f"Room {room}: Not Checked"

            # Create button with status
            btn = Button(text=status_text, size_hint_y=None, height=40)
            btn.bind(on_press=lambda x, room=room: self.check_room(room))
            
            # Color code based on status
            if all_checked:
                btn.background_color = (0, 1, 0, 1)  # Green for completed
            elif partially_checked:
                btn.background_color = (1, 1, 0, 1)  # Yellow for partial
            else:
                btn.background_color = (1, 0, 0, 1)  # Red for not checked
            
            room_buttons.add_widget(btn)

        # Add room buttons to the scroll view
        scroll_view.add_widget(room_buttons)
        content.add_widget(scroll_view)
        
        self.show_popup_content(f'Check Floor {floor}', content)

    def check_room(self, room):
        content = BoxLayout(orientation='vertical')
        self.add_navigation(content, f'Check Room {room}')
        
        buttons_layout = BoxLayout(orientation='vertical')
        room_details = floors[self.current_floor][room]

        for item, count in room_details.items():
            for i in range(count):
                item_status = self.room_status[room][item.lower()][i]['status']
                item_layout = BoxLayout(orientation='horizontal')

                ok_btn = Button(text='OK')
                issue_btn = Button(text='Issue')
                notes_btn = Button(text='Notes')

                ok_btn.bind(on_press=lambda x, item=item, i=i: self.save_result(room, item.lower(), i,'OK'))
                issue_btn.bind(on_press=lambda x, item=item, i=i: self.save_result(room, item.lower(), i, 'ISSUE'))
                notes_btn.bind(on_press=lambda x, item=item, i=i: self.show_notes_input(room, item.lower(), i))

                item_layout.add_widget(Label(text=f'{item.capitalize()} {i + 1}: {item_status or "Not checked"}'))
                item_layout.add_widget(ok_btn)
                item_layout.add_widget(issue_btn)
                item_layout.add_widget(notes_btn)

                buttons_layout.add_widget(item_layout)

        content.add_widget(buttons_layout)
        self.show_popup_content(f'Check Room {room}', content)

    def save_result(self, room, item, index, result):
        self.room_status[room][item][index]['status'] = result
        self.save_current_state()
        self.show_room_check(self.current_floor)

    def show_notes_input(self, room, item, index):
        layout = BoxLayout(orientation='vertical')
        existing_note = self.room_status[room][item][index]['notes']
        text_input = TextInput(hint_text='Enter your notes here', text=existing_note)
        layout.add_widget(text_input)

        btn_save = Button(text='Save')
        btn_save.bind(on_press=lambda x: self.save_notes(room, item, index, text_input.text))
        layout.add_widget(btn_save)

        self.show_popup('Notes Input', layout)

    def save_notes(self, room, item, index, notes):
        self.room_status[room][item][index]['notes'] = notes
        logging.info(f"Saved notes for Room {room}, {item.capitalize()} {index + 1}: {notes}")
        self.save_current_state()
        self.dismiss_popup()

    def save_current_state(self):
        try:
            # Save to the default state file
            with open(DEFAULT_CSV_FILENAME, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Room', 'Item', 'Index', 'Status', 'Notes'])  # Header
                for room, items in self.room_status.items():
                    for item, statuses in items.items():
                        for index, status in enumerate(statuses):
                            if status['status']:  # Save only non-empty statuses
                                writer.writerow([room, item, index, status['status'], status['notes']])
                                logging.debug(f"Saved to state: Room {room}, Item {item}, Index {index}, Status {status['status']}, Notes: {status['notes']}")

            # Save to the most recent check results file
            if hasattr(self, 'csv_file') and self.csv_file:
                with open(self.csv_file, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Room', 'Item', 'Index', 'Status', 'Notes'])  # Header
                    for room, items in self.room_status.items():
                        for item, statuses in items.items():
                            for index, status in enumerate(statuses):
                                if status['status']:  # Save only non-empty statuses
                                    writer.writerow([room, item, index, status['status'], status['notes']])
                                    logging.debug(f"Saved to check file: Room {room}, Item {item}, Index {index}, Status {status['status']}, Notes: {status['notes']}")

            logging.info("Current state and check file saved successfully.")
        except Exception as e:
            logging.error(f"Error saving current state or check file: {e}")

    def dismiss_popup(self):
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()

class BuildingCheckApp(App):
    def build(self):
        return MainScreen()

if __name__ == '__main__':
    BuildingCheckApp().run()