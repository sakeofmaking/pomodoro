import logging
import os
import csv
from datetime import datetime, timedelta
import time
import curses
import pygetwindow as gw


# Configure logging
logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")


# Variables
header = r'''
 ____  ____  _      ____  ____  ____  ____  ____
/  __\/  _ \/ \__/|/  _ \/  _ \/  _ \/  __\/  _ \
|  \/|| / \|| |\/||| / \|| | \|| / \||  \/|| / \|
|  __/| \_/|| |  ||| \_/|| |_/|| \_/||    /| \_/|
\_/   \____/\_/  \|\____/\____/\____/\_/\_\\____/
'''
char_digits = [
'''
 ██████ 
██  ████
██ ██ ██
████  ██
 ██████ 
''',
'''
   ██   
  ███   
   ██   
   ██   
   ██   
''',
'''
██████  
     ██ 
 █████  
██      
███████ 
''',
'''
██████  
     ██ 
 █████  
     ██ 
██████  
''',
'''
██   ██ 
██   ██ 
███████ 
     ██ 
     ██ 
''',
'''
███████ 
██      
███████ 
     ██ 
███████ 
''',
'''
 ██████  
██      
███████ 
██    ██
 ██████ 
''',
'''
███████ 
     ██ 
    ██  
   ██   
   ██   
''',
'''
 █████  
██   ██ 
 █████  
██   ██ 
 █████  
''',
'''
 █████  
██   ██ 
 ██████ 
     ██ 
 █████  
'''
]
timer1_min, timer2_min, daily_goal_min, daily_complete_min, last_reset = 25, 5, 360, 0, ''  # Default values
menu_options = [
    'Exit',
    f'Start {timer1_min} min work timer',
    f'Start {timer2_min} min break timer',
    'Settings'
]
data_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(data_dir, 'data.csv')
remaining_min = 0


def display_menu(meat, progress):
    '''Display menu around meat content'''
    global header
    os.system('cls')  # Clear screen
    print(f'\033[1;32m{header}\033[0m')  # Print header in green
    print('█' * progress)
    print(meat)


def generate_meat(options):
    '''Generate meat content for menu'''
    meat = ''
    for index, option in enumerate(options):
        meat += f'\t[{index}] {option}\n'
    return meat


def display_timer(stdscr, duration_min, progress, work_flag=True):
    '''Use cursor to display timer'''
    global char_digits, header, remaining_min
    # Clear screen
    curses.curs_set(0)  # Hide cursor
    stdscr.nodelay(True)  # Don't block on input
    stdscr.timeout(100)  # Refresh every 100ms

    # Setup timer
    split_digits = [char.strip('\n').splitlines() for char in char_digits]
    num_lines = len(split_digits[0])
    duration_sec = duration_min * 60
    end_time = datetime.now() + timedelta(seconds=duration_sec)

    while datetime.now() < end_time:
        remaining = end_time - datetime.now()  # Update remaining time
        if remaining.seconds > 60:
            digit1 = remaining.seconds // 60 // 10
            digit2 = (remaining.seconds // 60) % 10
        else:
            digit1 = remaining.seconds // 10
            digit2 = remaining.seconds % 10
        
        stdscr.clear()  # Clear the screen buffer
        height, width = stdscr.getmaxyx()  # Get screen dimensions
        curses.start_color()  # Enable color mode
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Define color pair
        stdscr.addstr(0, 0, header, curses.color_pair(1))  # Print header in green
        stdscr.addstr(7, 0, '█' * progress, curses.color_pair(1))  # Print progress bar')

        for i in range(num_lines):
            stdscr.addstr((height // 2) + i - 3, width // 2 - 8, split_digits[digit1][i] + '  ', curses.color_pair(1))
            stdscr.addstr((height // 2) + i - 3, width // 2 + len(split_digits[digit1][i] + '  ') - 8, split_digits[digit2][i] + '  ', curses.color_pair(1))

        stdscr.refresh()  # Refresh the screen with new content

        try:
            key = stdscr.getch()
            if key == ord('q'):
                break
        except:
            pass

        time.sleep(0.1)

    remaining_min = round(remaining.seconds / 60)
    if work_flag:
        add_to_daily_total(duration_min - remaining_min)
    if remaining_min == 0:
        focus_cli_window()
        curses.wrapper(flash_screen)


def read_settings(file_path):
    '''Read settings from CSV'''
    with open(file_path, 'r', newline='') as file:
        reader = csv.reader(file)
        first_row = next(reader, [])
        # If timestamp is missing, default to empty string
        if len(first_row) < 5:
            first_row.append('')
        # Convert first four values to int, fifth to str
        value1 = int(first_row[0])
        value2 = int(first_row[1])
        value3 = int(first_row[2])
        value4 = int(first_row[3])
        value5 = first_row[4]
        return value1, value2, value3, value4, value5


def add_to_daily_total(completed_min):
    '''Add completed timer to daily total'''
    global data_file
    timer1_min, timer2_min, daily_goal_min, daily_complete_min, last_reset = read_settings(data_file)  # Read current daily total from CSV
    daily_complete_min += completed_min
    updated_settings = (timer1_min, timer2_min, daily_goal_min, daily_complete_min, last_reset)

    # Update daily total in CSV
    with open(data_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows([updated_settings])


def reset_daily_total():
    '''Reset daily total and update timestamp'''
    global data_file
    timer1_min, timer2_min, daily_goal_min, _, _ = read_settings(data_file)
    daily_complete_min = 0
    last_reset = datetime.now().isoformat(timespec='seconds')
    updated_settings = (timer1_min, timer2_min, daily_goal_min, daily_complete_min, last_reset)
    with open(data_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(updated_settings)


def check_and_reset_daily_total():
    '''Reset daily total if last reset was before today'''
    timer1_min, timer2_min, daily_goal_min, daily_complete_min, last_reset = read_settings(data_file)
    try:
        last_reset_dt = datetime.fromisoformat(last_reset)
    except Exception:
        last_reset_dt = datetime.min
    midnight_today = datetime.combine(datetime.today(), datetime.min.time())
    if last_reset_dt < midnight_today:
        reset_daily_total()


def focus_cli_window():
    '''Bring the CLI window into focus'''
    # Get the current console window title
    title = os.path.basename(os.getenv('COMSPEC', 'cmd.exe'))
    # Try to find a window with 'cmd' or 'powershell' in the title
    for win in gw.getAllWindows():
        if win.title and ('cmd' in win.title.lower() or 'powershell' in win.title.lower()):
            try:
                if win.isMinimized:
                    win.restore()  # Restore the window if minimized
                win.activate()  # Bring it to the foreground
            except Exception as e:
                logging.info(f'Could not focus CLI window: {e}')
            break


def flash_screen(stdscr, flashes=5, delay=0.2):
    '''Flash the screen green then black using curses'''
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Green background
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Black background

    for _ in range(flashes):
        stdscr.bkgd(' ', curses.color_pair(1))
        stdscr.clear()
        stdscr.refresh()
        time.sleep(delay)
        stdscr.bkgd(' ', curses.color_pair(2))
        stdscr.clear()
        stdscr.refresh()
        time.sleep(delay)


def main():
    user_input = ''
    while user_input != '0':
        check_and_reset_daily_total()
        timer1_min, timer2_min, daily_goal_min, daily_complete_min, last_reset = read_settings(data_file)
        progress = round((daily_complete_min * 48) / daily_goal_min)  # Update progress
        menu_options = [  # Update menu options with latest settings
            'Exit',
            f'Start {timer1_min} min work timer',
            f'Start {timer2_min} min break timer',
            'Settings'
        ]
        if remaining_min > 0:
            menu_options.append(f'Continue {remaining_min} min timer')

        # Display menu
        display_menu(generate_meat(menu_options), progress)
        user_input = input('>>> ')

        # Execute user selection
        if user_input == '1':
            curses.wrapper(lambda stdscr: display_timer(stdscr, timer1_min, progress, True))
        elif user_input == '2':
            curses.wrapper(lambda stdscr: display_timer(stdscr, timer2_min, progress, False))
        elif user_input == '3':
            display_menu('Settings not implemented yet.')
        elif user_input == '4':
            curses.wrapper(lambda stdscr: display_timer(stdscr, remaining_min, progress))


if __name__ == '__main__':
    main()
