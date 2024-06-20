import multiprocessing as mp
from queue import Queue, Empty
from FileServerLib import FileServerLib
from watchdog.observers import Observer     # Ref: https://stackoverflow.com/questions/57840072/how-to-check-for-new-files-in-a-folder-in-python
from watchdog.events import FileSystemEvent, FileSystemEventHandler
import os, sys
import signal
from Audio import Audio
import keyboard
import time
from sshkeyboard import listen_keyboard
import json, requests, re

""" This version may have a better real time performance, but it also has a  loading,
    which may make it even slower than threading ver. if the # of cores isn't enough.
"""


TIME_OUT = 1
SLEEP_DUR = 0     # Don't even need to sleep on my PC

def press(key, queue):
    # if key == "up":
    #     print("up pressed")
    # elif key == "down":
    #     print("down pressed")
    # elif key == "left":
    #     print("left pressed")
    # elif key == "right":
    #     print("right pressed")
    if key in ["y", "t", "z"]:
        print(f"{key} pressed")
        queue.put(key)

# Define a signal handler that handle ctrl+c signal
def end(flags):
    if not flags['end'] or not flags['music_stop']:
        print("Ending Processs...")
        flags['end'] = True
        flags['music_stop'] = True

# Define a signal handler that handle start music button
def music_start(flags):
    if not flags['music_start']:
        print("Starting music mode...")
        flags['music_start'] = True
        flags['music_stop'] = False

# Define a signal handler that handle music button
def music_stop(flags):
    if not flags['music_stop']:
        print("Terminating music mode...")
        flags['music_stop'] = True
        flags['music_start'] = False

# Just for safe, I wrote a function works with keyboard instead of signal
def keyboard_sense(flags, queue, message_queue):
    """ Monitor the input from keyboard. It is crucial for terminating the whole process.

    Args:
        flags (dict): shared flags
    """
    music_begin = 'y'
    music_end = 't'
    interrupt = 'z'
    print('Start keyboard_sense')
    while True: 
        # Break or not
        end_flag = flags['end']
        if end_flag:
            print("End keyboard sensing.")
            break
        try:
            key = queue.get(timeout=0.1)
            if key == music_begin:
                print('y is pressed')
                music_start(flags)
            if key == music_end:
                print('t is pressed')
                music_stop(flags)
            if key == interrupt:
                print('z is pressed')
                end(flags)
        except Empty:
            # print('There are no keyboard input')
            pass

def emoji2screen(faces) -> None:
    for face in faces:
        with open('./awtrix/notify.json', 'r+') as f:
            data = json.load(f)
            data['speed'] = 1
            data['data'] = face
            data['fallingText'] = False
            data['force'] = True
            url = 'http://localhost:7000/api/v3/notify'
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers = headers, json = data)
            # Success!
            # print(response.status_code)
            # print(response.json)

def animation_end() -> None:
    """Not defined yet.
    """
    pass
def animation_sleeping() -> None:
    """Not defined yet.
    """
    pass
def animation_file_created() -> None:
    """Not defined yet.
    """
    emoji2screen(faces)
    pass
def animation_file_deleted() -> None:
    """Not defined yet.
    """
    # ......
    
    # flags['file_deleted'] = False
    pass

def animation_waiting() -> None:
    """Not defined yet.
    """
    faces = [' >.< ', ' ^.< ', ' >.^ ', ' >.< ', '>.<  ', ' >.< ', '  >.<', ' >.< ']
    emoji2screen(faces)

        
    pass
def animation_falling() -> None:
    """Not defined yet.
    """
    pass
def show_message(message) -> None:
    """Not defined yet.
    """
    # For testing
    print(message)
    # return
    
    # notify.json as a template
    # sentence = re.split(r'(\W+)', message)
    with open('./awtrix/notify.json', 'r+') as f:
        data = json.load(f)
        data['data'] = message
        data['speed'] = 20
        url = 'http://localhost:7000/api/v3/notify'
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers = headers, json = data)
    """
    for word in sentence:
        if word.strip():  
            # one word send a post, let it queue in awtrix 
            with open('./awtrix/notify.json', 'r+') as f:
                data = json.load(f)
                data['data'] = word
                # data['speed'] = 65
                url = 'http://localhost:7000/api/v3/notify'
                headers = {
                    'Content-Type': 'application/json'
                }
                response = requests.post(url, headers = headers, json = data)
                # Success!
                # print(response.status_code)
                # print(response.json)
            pass
    """
def audio_mode(flags, message_queue):
    """ Audio subprocess. It will start running at the beginning and pool the "music_start" flag.
        Once the flag is set, it will start fetching mic input.

    Args:
        flags (dict): shared flags
    """
    # Process main loop
    print('Start music')
    while True:
        # print(f'music start flag: {flags["music_start"]}')
        # Break or not
        end_flag = flags['end']
        if end_flag:
            print("End music.")
            break
        # Check if the music button has been pressed
        time.sleep(0.1)
        music_start_flag = flags['music_start']
        if not music_start_flag:
            continue
        # Input a title
        try:
            message_queue.put('Please say any name of song.')
            # print('Please say any name of song.')
            title = Audio.Speech_to_Text()
            print(f'Seaching {title}....')
            # title = 'Never gonna give you up'
            # Search video
            video_info, status = Audio.yt_search_video(title, message_queue)
            if not status:
                continue
            # Play video
            Audio.yt_play_video_with_transcript(video_info, flags, message_queue)
        except Exception as e:
            print(e)
            message_queue.put('Error when inputting mic...')
            # print('Error when inputting mic...')
            continue
        finally:
            flags['music_start'] = False


def display_pet(flags, message_queue):
    """Determine the pet's status on the screen. (maybe by changing icon or something)

    Args:
        flags (dict): shared flags
    """
    print('Start pet')
    while True:
        PET_SLEEP = 1
        time.sleep(PET_SLEEP)
        # Break or not
        end_flag = flags['end']
        # print('Start pet')
        if end_flag:
            print("End displaying pet.")
            animation_end()
            break
        # If in music mode, no pet is displayed
        music_start_flag = flags['music_start']
        if music_start_flag:
            continue
        # Sleep or not
        if FileServerLib.check_no_connections():
            animation_sleeping()
            continue
        # Falling or not
        falling_flag = flags['falling']
        if falling_flag:
            animation_falling()
            continue
        # File created or not
        file_created_flag = flags['file_created']
        if file_created_flag:
            animation_file_created()
            flags['file_created'] = False
        # File deleted or not
        file_deleted_flag = flags['file_deleted']
        if file_deleted_flag:
            animation_file_deleted() 
            flags['file_deleted'] = False
        animation_waiting()
        
def display_message(flags, message_queue):
    """Get a message from the queue and show it on the screen.

    Args:
        flags (dict): Shared flags
        message_queue (mp.queue): A synchronized queue to store message
    """
    print('Start message')
    while True:
        # Break or not
        end_flag = flags['end']
        if end_flag:
            print("End displaying message.")
            message_queue.put("Press ESC to end the process")
            # print("Press ESC to end the process")
            break
        # Show message (blocking with timeout for efficiency)
        try:
            message =  message_queue.get(timeout=TIME_OUT)
            show_message(message)
            # print(message)
            # message_queue.task_done()
        except Empty:
            pass



def monitor_Process(folder_path, flags, message_queue):
    """Monitor the folder_path and check if there're any files created.

    Args:
        folder_path (str): The path to the folder you want to monitor
    """
                
    event_handler = FileServerLib.MyHandler(folder_path, flags, message_queue)
    observer = Observer()
    observer.schedule(event_handler, path=folder_path, recursive=False)
    observer.start()

    print('Start monitor')
    while True:
        end_flag = flags['end']
        time.sleep(SLEEP_DUR)     # Sleep to avoid starvation
        if end_flag:
            print(f"Stop monitoring {folder_path}.")
            break

if __name__ == "__main__":
    with open('./awtrix/remove.json', 'r+') as f:
        data = json.load(f)
        url = 'http://localhost:7000/api/v3/notify'
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers = headers, json = data)
    print(response.status_code)
    # print('good')
    # TODO: Add IMU related functions & (probably) https request sender.
    
    # listen_keyboard(on_press=press)

    mng = mp.Manager()
    flags = mng.dict({'file_created':False, 'file_deleted':False, 'end':False, 'falling':False, 'music_stop':False, 'music_start':False})
    message_queue = mp.Queue()
    key_queue = mp.Queue()


    folder_path = "/media/share/"
    # folder_path = os.path.abspath(folder_path)
    # Create file_monitor Process
    file_monitor_Process = mp.Process(target=monitor_Process, args=(folder_path, flags, message_queue,))
    # Create display_pet Process
    display_pet_Process = mp.Process(target=display_pet, args=(flags,message_queue,))
    # Create display_text Process
    display_message_Process = mp.Process(target=display_message, args=(flags, message_queue,))
    # Create keyboard_sense Process
    keyboard_sense_Process = mp.Process(target=keyboard_sense, args=(flags, key_queue, message_queue))
    # Create audio_mode Process
    audio_mode_Process = mp.Process(target=audio_mode, args=(flags, message_queue))
    
    # Start Processs
    file_monitor_Process.start()
    display_pet_Process.start()
    display_message_Process.start()
    keyboard_sense_Process.start()
    audio_mode_Process.start()
    
    time.sleep(1)
    print('-------------------------------')
    
    listen_keyboard(on_press=lambda key: press(key, key_queue))
    # Wait until Processs end
    file_monitor_Process.join()
    display_pet_Process.join()
    display_message_Process.join()
    keyboard_sense_Process.join()
    audio_mode_Process.join()
    
    show_message("Processs terminated successfully!")
    # print("Processs terminated successfully!")
    sys.exit(0)