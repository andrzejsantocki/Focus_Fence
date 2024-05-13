from libs_set import *
import BehaviourControl as beh


# Set Up Environmental Variables

workspace_id = os.getenv('workspace_id')
workspace_id_int = int(workspace_id)
togg_nickname = os.getenv('togg_nickname')
togg_pass= os.getenv('toggl_password')



# Function to simulate button click on Enter key press
def on_enter_press(event):
    event.widget.invoke()

# Function to clear the input box
def clear_entry():
    entry.delete(0, tk.END)

# Function to show the red dot
def show_red_dot():
    indicator_canvas.itemconfigure(red_dot, state='normal')

# Function to hide the red dot
def hide_red_dot():
    indicator_canvas.itemconfigure(red_dot, state='hidden')

# Function to check if the window is maximized
def check_on_top(root):
    print(' root.state()', root.state())
    if root.state() == 'iconic':
            root.state('normal')


# Function to run the check every 60 seconds
def schedule_check(root):
    check_on_top(root)
    delay_between_checks =random.randint(60000, 360000)
    print(delay_between_checks)
    root.after(delay_between_checks, schedule_check, root)


# Function to move the window
def move_window(event):
    root.geometry('+{0}+{1}'.format(event.x_root, event.y_root))

def minimize_window(title):
    try:
        root.overrideredirect(False)
        root.state('iconic')

    except IndexError:
        print(f"No window with title '{title}' found.")

def check_window_state(root):
    if root.state() == 'normal':
        root.overrideredirect(True)
    # Schedule the check_window_state function to run again after 1000ms
    root.after(100, check_window_state, root)



def on_drag(event):
    # Calculate the new window position
    x = root.winfo_pointerx() - offset_x
    y = root.winfo_pointery() - offset_y
    # Move the window to the new position
    root.geometry(f'+{x}+{y}')

def start_drag(event):
    global offset_x, offset_y
    # Record the offset between the window top-left corner and the current mouse position
    offset_x = event.x
    offset_y = event.y

def defocus_buttons():
    # If the focus is on a button, set the focus back to the root window
    print("I will try to defocus buttosn")
    if root.focus_get() in [start_button, stop_button]:
        print(' root.focus_get() in [start_button, stop_button]:')
        root.focus_set()



# Function to create a custom title bar
def create_custom_title_bar(root, title, color):
    # Remove the title bar
    root.overrideredirect(True)

    # Create a title bar frame
    title_bar = tk.Frame(root, bg=color, relief='raised', bd=0)

    # Create a label for the title
    title_label = tk.Label(title_bar, text=title, bg=color, fg='white')


    # Create a close button on the title bar
    close_button = tk.Button(title_bar, text='X', command=root.destroy, bg=color, fg='white')
    close_button.pack(side=tk.RIGHT)

    # Create a minimize button on the custom title bar
    minimize_button = tk.Button(title_bar, text='_', command=lambda: minimize_window("Focus Fence Toggl"), bg='#333333', fg='white')
    minimize_button.pack(side=tk.RIGHT, padx=2, pady=2)

    # Pack the widgets
    title_bar.pack(fill=tk.X)
    title_label.pack(side=tk.LEFT, padx=10)

    minimize_button.pack(side=tk.RIGHT)
    # Bind title bar motion to the move window function
    title_bar.bind('<B1-Motion>', move_window)


# Function to start a new time entry with the description provided by the user
global toggl_entry_running
def start_time_entry(username, password, description,entry_widget):
    if description == "" or timer_value == 0: # Start Only If Timer is set and Input Bos is not empty
        beh.sound_window_if_empty()
    else:
        credentials = (username, password)
        headers = {'Content-Type': 'application/json'}
        data = {
            'created_with': 'Tkinter App',
            'description': description,
            'tags': [],
            'billable': False,
            'workspace_id': 4895576,
            'duration': -1,
            'start': datetime.now(timezone.utc).isoformat(),
            'stop': None
        }

        response = requests.post(
            f'https://api.track.toggl.com/api/v9/workspaces/{workspace_id_int}/time_entries',
            json=data,
            headers=headers,
            auth=credentials
        )
        if response.status_code == 200:
            print('Time entry started successfully.')
            show_red_dot()
            root.update_idletasks()  # Update the mainloop to reflect changes
            start_timer()
            toggl_entry_running = True
        else:
            print(f'Failed to start time entry. Status code: {response.status_code}')
            print(f'Response: {response.text}')

    root.focus_set()  # Set focus back to the main window

# Function to stop the current time entry and clear the input line
def stop_current_time_entry(username, password, entry_widget):
    credentials = (username, password)
    headers = {'Content-Type': 'application/json'}
    current_entry_response = requests.get(
        'https://api.track.toggl.com/api/v9/me/time_entries/current',
        auth=credentials
    )
    if current_entry_response.status_code == 200 and current_entry_response.json():
        current_entry_data = current_entry_response.json()
        if 'id' in current_entry_data and current_entry_data['id']:
            current_entry_id = current_entry_data['id']
            workspace_id = current_entry_data['workspace_id']
            data = {'stop': datetime.now(timezone.utc).isoformat()}
            stop_response = requests.put(
                f'https://api.track.toggl.com/api/v9/workspaces/{workspace_id}/time_entries/{current_entry_id}',
                json=data,
                headers=headers,
                auth=credentials
            )
            if stop_response.status_code == 200:
                print('Time entry stopped successfully.')
                entry_widget.delete(0, tk.END)  # Clear the input line
                hide_red_dot()
                root.update_idletasks()  # Update the mainloop to reflect changes
                toggl_entry_running = False
                reset_timer()
            else:
                print(f'Failed to stop time entry. Status code: {stop_response.status_code}')
                print(f'Response: {stop_response.text}')
        else:
            print('No running time entry found.')
    else:
        print('Failed to retrieve the current time entry or no JSON response received.')

    root.focus_set()  # Set focus back to the main window



# Timer Functionality
def play_sound():
    # Function to play sound for 5 seconds
    print("Beep! (sound plays for 5 seconds)")
    # Simulate sound playing
    time.sleep(5)  # This would block the GUI; replace with actual non-blocking sound play in real use


timer_value = 0
timer_active = False
save_timer_id = None  # Ensure the timer ID is initialized
display_timer_id = None  # Initialize display timer ID
timer_blocked = False

def increment_time(event=None):
    global timer_value, timer_blocked, save_timer_id
    # Only increment if the timer is not blocked
    if not timer_blocked:
        if timer_value <45:
            timer_value += 5
        else:
            timer_value += 15
        timer_display.config(text=f"{timer_value}")  # Display minutes more clearly

        # Block further increments
        timer_blocked = False
        # Cancel any previous unexecuted after calls to block increment
        if save_timer_id:
            root.after_cancel(save_timer_id)
        # Set a timer to unblock after 5 seconds
        save_timer_id = root.after(10000, toggle_increment)

def toggle_increment():
    global timer_blocked   
    # Allow incrementing after 5 seconds
    if timer_blocked == True:
        timer_blocked = False
    else:
        timer_blocked = True


def start_timer():
    global timer_active, display_timer_id, timer_value
    # Only start if the timer is not active and has a value greater than zero
    print('I will start countdows')
    if not timer_active and timer_value > 0:
        timer_active = True
        timer_value += 1
        countdown()

def countdown():
    global timer_value, timer_display, timer_active
    if timer_value > 0:
        root.after(60000, countdown)  # Continue countdown each minute
        timer_value -= 1
        update_display()
    else:
        timer_active = False
        timer_display.config(text="")
        play_sound()  # Assuming a play_sound function exists to alert the user

def reset_timer():
    global timer_value, timer_display, timer_active
    timer_value = 0
    toggle_increment()
    play_sound('static/sounds/sound.mp3')
    update_display()
    stop_current_time_entry()

def update_display():
    # Update the timer display with the current value
    timer_display.config(text=f"{timer_value}")

def play_sound(filename):
    # Initialize Pygame Mixer
    pygame.mixer.init()
    # Load the sound file
    sound = pygame.mixer.Sound(filename)
    # Play the sound
    sound.play()
    # Keep the script running until the sound is playing
    while pygame.mixer.get_busy():  
        pygame.time.Clock().tick(10)  # Use a small delay to prevent high CPU usage
    
    # Quit the mixer
    pygame.mixer.quit()



#button functions

def update_red_dot_position(event):
    # Calculate the new right edge based on the current window width
    right_edge = event.width - (event.width/7) + 300  # 40 pixels from the right edge
    print(event.width)
    indicator_canvas.place(x=right_edge, y=80)


# Create the main window

try:
    # This will create a lock file at a location that other instances can check
    single_instance = singleton.SingleInstance()
except singleton.SingleInstanceException:
    # If this exception is raised, it means there's already an instance running
    sys.exit("Another instance of the app is already running.")


try:
    root = tk.Tk()
    width_window = 350 #350
    height_window = 130 #130
    root.title("Focus Fence Toggl")
    root.attributes('-topmost', True)
    
    # Set the transparency value (0.5 for 50% transparency)
    root.attributes('-alpha', 0.75)

    # Set the initial size and position of the window (width x height + x_offset + y_offset)
    root.geometry(f'{width_window}x{height_window}+1500+200')

    #timer_display = ttk.Label(root, text='0', font=('Helvetica'),  foreground='white')
    # Timer display configuration with a fixed size
    timer_display = ttk.Label(root, text='0', style='TLabel',font=('Helvetica'),  width=3)
    timer_display.pack(side='left', padx=(10, 10), pady=2, anchor='center')


    timer_display.bind('<Button-1>', increment_time)



    # Set the theme to 'clam' which supports dark mode
    style = ttk.Style()
    style.theme_use('clam')

    # Configure the colors for dark mode
    style.configure('TButton', background='#333333', foreground='white', borderwidth=1)
    style.configure('TFrame', background='#333333')
    style.configure('TLabel', background='#333333', foreground='white')
    style.configure('TEntry', background='#555555', foreground='white', fieldbackground='#555555', borderwidth=1)

    # Configure the colors for the canvas
    canvas_color = '#333333'
    root.configure(bg=canvas_color)

    # Configure the style for the focused state of the buttons
    style.map('TButton',
              background=[('active', '#333333'), ('focus', 'grey')],
              foreground=[('focus', 'white')],
              bordercolor=[('focus', 'grey')])



    # Create a custom title bar with the specified color
    create_custom_title_bar(root, "Focus Fence Toggl", '#333333')

    # Add the schedule_check call in your main code
    schedule_check(root)
    # Disable resizing the GUI by passing in False for both the x and y dimensions
    root.resizable(False, False)

    # Define a larger font for the input box
    entry_font = tkFont.Font(size=12)

    # Create an entry widget for user input
    entry = ttk.Entry(root, width=35, font=entry_font)
    entry.pack(padx=10, pady=10)

    # Create a frame to hold the buttons in a horizontal layout
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)



    # Create a canvas for the red dot indicator
    indicator_canvas = tk.Canvas(root, width=20, height=20, bg='#333333', highlightthickness=0)
    red_dot = indicator_canvas.create_oval(5, 5, 15, 15, fill='red')
    indicator_canvas.itemconfig(red_dot, state='hidden')  # Initially hide the red dot
    indicator_canvas.pack(side='top', pady=5)  # Pack or place your canvas as needed

    # Bind the resize event to dynamically adjust the red dot's position
    root.bind('<Configure>', update_red_dot_position)

    # Position the canvas in the top left corner of the window
    # Position the red dot indicator more prominently

    # Create a 'Start' button
    start_button = ttk.Button(button_frame, text="Start",  width=15, command=lambda: start_time_entry(togg_nickname, togg_pass, entry.get(),entry))
    start_button.pack(side=tk.LEFT, padx=5)
    start_button.configure(takefocus=1)

    # Create a 'Stop' button
    stop_button = ttk.Button(button_frame, text="Stop", width=15, command=lambda: [stop_current_time_entry(togg_nickname, togg_pass, entry), clear_entry()])
    stop_button.pack(side=tk.LEFT, padx=5)
    stop_button.configure(takefocus=1)


    # Create a transparent icon as a temporary file
    ICON = zlib.decompress(base64.b64decode('eJxjYGAEQgEBBiDJwZDBy''sAgxsDAoAHEQCEGBQaIOAg4sDIgACMUj4JRMApGwQgF/ykEAFXxQRc='))
    _, ICON_PATH = tempfile.mkstemp()
    with open(ICON_PATH, 'wb') as icon_file:
        icon_file.write(ICON)


    # Bind Enter key to simulate the button click
    start_button.bind('<Return>', on_enter_press)
    stop_button.bind('<Return>', on_enter_press)

    # Set focus on the 'Start' button to react to Tab and Enter keys
    start_button.focus_set()

    # Allow the Tab key to navigate through the buttons
    root.bind_class("TButton", "<FocusIn>", lambda e: e.widget.configure(takefocus=1))
    #check_window_state(root)


    check_window_state(root)


    # Bind the mouse click event to the function that starts the drag
    root.bind('<Button-1>', start_drag)
    # Bind the mouse movement event to the function that performs the drag
    root.bind('<B1-Motion>',  on_drag)


    # Start the Tkinter event loop
    root.mainloop()
    # Remove the temporary file after the app closes
    os.remove(ICON_PATH)
except (PermissionError,KeyboardInterrupt):
    'pass'