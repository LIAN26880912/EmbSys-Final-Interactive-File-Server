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
    # ......
    
    # flags['file_created'] = False
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
    for face in faces:
        with open('./awtrix/notify.json', 'r+') as f:
            data = json.load(f)
            data['speed'] = 1
            data['data'] = face
            url = 'http://localhost:7000/api/v3/notify'
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(url, headers = headers, json = data)
            print(response.status_code)
            print(response.json)
        pass

        
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
    sentence = re.split(r'(\W+)', message)
    for word in sentence:
        if word.strip():  
            # one word send a post, let it queue in awtrix 
            with open('./awtrix/notify.json', 'r+') as f:
                data = json.load(f)
                data['data'] = word
                url = 'http://localhost:7000/api/v3/notify'
                headers = {
                    'Content-Type': 'application/json'
                }
                response = requests.post(url, headers = headers, json = data)
                print(response.status_code)
                print(response.json)
            pass


def yt_play_video_with_transcript(video_info, flags, message_queue):
    """ Play video with VLC Media Player (With transcript version)

    Args:
        video_info (dict): The info of the video (From yt_search_video())
    """
    url = video_info['link']
    video = pafy.new(url)
    best = video.getbest()
    playurl = best.url
    Instance = vlc.Instance()
    player = Instance.media_player_new()
    Media = Instance.media_new(playurl)
    Media.get_mrl()
    player.set_media(Media)
    transcript = Transcript.get(url)['segments']
    transcript_len = len(transcript)
    
    # Start playing video.
    subscript = ""
    i = 0
    if player.play() == 0:   # Successful play
        time.sleep(0.5)
        print("----------------- Start subscript ---------------------")
        while player.is_playing():
            # Break or not
            end_flag = flags['end']
            stop_flag = flags['music_stop']
            if end_flag or stop_flag:
                break
            # Continue to play music(video)
            cur_time = player.get_time()     # In ms
            if i < transcript_len and cur_time >= int(transcript[i]['startMs']-500):
                subscript = transcript[i]['text']
                message_queue.put(subscript)
                # print(subscript)
                i += 1
            # Hold for 0.1 sec
            time.sleep(0.1)
        print("----------------- End subscript ---------------------")
        message_queue.put("Video end")
        # print("Video end")
        # player.stop()
    else:   # Failed playing
        print("Failed to play the video")
        
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
            # title = Audio.Speech_to_Text()
            title = 'Never gonna give you up'
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
        time.sleep(SLEEP_DUR)
        # Break or not
        end_flag = flags['end']
        # print('Start pet')
        if end_flag:
            print("End displaying pet.")
            animation_end()
            break
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
            break
        # Show message (blocking with timeout for efficiency)
        try:
            message =  message_queue.get(timeout=TIME_OUT)
            show_message(message)
            # print(message)
            # message_queue.task_done()
        except Empty:
            pass

class MyHandler(FileSystemEventHandler):
    def __init__(self, path, flags, message_queue):
        super().__init__()
        self.path = path
        self.last_modified = time.time()
        self.flags = flags
        self.message_queue = message_queue

    def on_any_event(self, event):
        pass
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        # Acquire the lock and set the flag
        self.flags['file_deleted'] = True
        # Determine and print system message
        message = None
        new_dir = event.src_path.split('/')[-1]
        num_deleted = sum([len(files) for r, d, files in os.walk(new_dir)])
        if num_deleted <= 1:
            message = f"{new_dir} has been deleted."
            # print(message)
        else:
            message = f"{num_deleted} files have been deleted."
            # print(message)
        self.message_queue.put(message)
        
    def on_created(self, event):
        # Acquire the lock and set the flag
        self.flags['file_created'] = True
        # Determine and print system message
        message = None
        new_dir = event.src_path.split('/')[-1]
        num_created = sum([len(files) for r, d, files in os.walk(new_dir)])
        if num_created <= 1:
            message = f"{new_dir} has been created."
            # print(message)
        else:
            message = f"{num_created} files have been created."
            # print(message)
        self.message_queue.put(message)

    def on_modified(self, event):
        if not event.is_directory and time.time()-self.last_modified > 1:
            self.message_queue.put(f"File modified: {event.src_path}")
            # print(f"File modified: {event.src_path}")


def monitor_Process(folder_path, flags, message_queue):
    """Monitor the folder_path and check if there're any files created.

    Args:
        folder_path (str): The path to the folder you want to monitor
    """
                
    event_handler = MyHandler(folder_path, flags, message_queue)
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
    print('good')
    # TODO: Add IMU related functions & (probably) https request sender.
    
    # listen_keyboard(on_press=press)

    mng = mp.Manager()
    flags = mng.dict({'file_created':False, 'file_deleted':False, 'end':False, 'falling':False, 'music_stop':False, 'music_start':False})
    message_queue = mp.Queue()
    key_queue = mp.Queue()


    folder_path = "."
    folder_path = os.path.abspath(folder_path)
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