import threading     
from queue import Queue, Empty
from FileServerLib import FileServerLib
from watchdog.observers import Observer     # Ref: https://stackoverflow.com/questions/57840072/how-to-check-for-new-files-in-a-folder-in-python
from watchdog.events import FileSystemEvent, FileSystemEventHandler
import os, sys
import signal
from Audio import Audio
import keyboard
import time


locks = {'file_created':threading.Lock(), 'file_deleted':threading.Lock(), 'end':threading.Lock(), 'falling':threading.Lock(), 'music_stop':threading.Lock()}
flags = {'file_created':False, 'file_deleted':False, 'end':False, 'falling':False, 'music_stop':False}
message_queue = Queue()
music_semaphore = threading.Semaphore(0)
TIME_OUT = 1
SLEEP_DUR = 0.5     # Sleep to avoid starvation

# Define a signal handler that handle ctrl+c signal
def end(signum, frame):
    flags['end'] = True
    flags['music_stop'] = True
    print("Ending Threads...")
# SIGINT means ctrl+c in linux
signal.signal(signal.SIGINT, end)       # Didn't work in Windows sometimes

# Define a signal handler that handle start music button
def music_start(signum, frame):
    print("Starting music mode...")
    music_semaphore.release()
# SIGUSR1 means a user defined signal in linux
#signal.signal(signal.SIGUSR1, music_start)

# Define a signal handler that handle music button
def music_stop(signum, frame):
    print("Terminating music mode...")
    with locks['music_stop']:
        flags['music_stop'] = True
# SIGUSR2 means another user defined signal in linux
#signal.signal(signal.SIGUSR2, music_stop)

# Just for safe, I wrote a function works with keyboard instead of signal
def keyboard_sense():
    music_begin = 'y'
    music_end = 't'
    interrupt = 'z'
    print('Start keyboard_sense')
    while True:
        # Break or not
        with locks['end']:
            end_flag = flags['end']
        if end_flag:
            print("End keyboard sensing.")
            break
        if keyboard.is_pressed(music_begin):
            music_start(0,0)
        if keyboard.is_pressed(music_end):
            music_stop(0,0)
        if keyboard.is_pressed(interrupt):
            end(0,0)

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
    pass
def animation_file_deleted() -> None:
    """Not defined yet.
    """
    pass
def animation_waiting() -> None:
    """Not defined yet.
    """
    pass
def animation_falling() -> None:
    """Not defined yet.
    """
    pass
def show_message() -> None:
    """Not defined yet.
    """
    pass


def yt_play_video_with_transcript(video_info):
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
            with locks['end']:
                end_flag = flags['end']
            # Access locks one-by-one to avoid deadlock
            with locks['music_stop']:
                stop_flag = flags['music_stop']
            if end_flag or stop_flag:
                break
            # Continue to play music(video)
            cur_time = player.get_time()     # In ms
            if i < transcript_len and cur_time >= int(transcript[i]['startMs']):
                subscript = transcript[i]['text']
                message_queue.put(subscript)
                print(subscript)
                i += 1
            # Hold for 0.1 sec
            time.sleep(0.1)
        print("----------------- End subscript ---------------------")
        print("Video end")
        # player.stop()
    else:   # Failed playing
        print("Failed to play the video")
    
def audio_mode():
    # Thread main loop
    print('Start music')
    while True:
        # Break or not
        with locks['end']:
            end_flag = flags['end']
        if end_flag:
            print("End music.")
            break
        # Check if the music button has been pressed
        acked = music_semaphore.acquire(timeout=TIME_OUT)
        if not acked:
            continue
        # Input a title
        title = Audio.Speech_to_Text()
        # Search video
        video_info, status = Audio.yt_search_video(title)
        if not status:
            continue
        # Play video
        yt_play_video_with_transcript(video_info)


def display_pet():
    print('Start pet')
    while True:
        time.sleep(SLEEP_DUR)
        # Break or not
        with locks['end']:
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
        with locks['falling']:
            falling_flag = flags['falling']
        if falling_flag:
            animation_falling()
            continue
        # File created or not
        with locks['file_created']:
            file_created_flag = flags['file_created']
        if file_created_flag:
            animation_file_created()
        # File deleted or not
        with locks['file_deleted']:
            file_deleted_flag = flags['file_deleted']
        if file_deleted_flag:
            animation_file_deleted() 
        animation_waiting()
        
def display_message():
    print('Start message')
    while True:
        # Break or not
        with locks['end']:
            end_flag = flags['end']
        if end_flag:
            print("End displaying message.")
            break
        # Show message (blocking with timeout for efficiency)
        try:
            message =  message_queue.get(timeout=TIME_OUT)
            show_message(message)
            print(message)
            message_queue.task_done()
        except Empty:
            pass

class MyHandler(FileSystemEventHandler):
    def __init__(self, path):
        super().__init__()
        self.path = path
    
    def on_any_event(self, event):
        pass
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        # Acquire the lock and set the flag
        with locks['file_deleted']:
            flags['file_deleted'] = True
        # Determine and print system message
        message = None
        new_dir = event.src_path.split('\\')[-1]
        num_deleted = sum([len(files) for r, d, files in os.walk(new_dir)])
        if num_deleted <= 1:
            message = f"{new_dir} has been deleted."
            print(message)
        else:
            message = f"{num_deleted} files have been deleted."
            print(message)
        message_queue.put(message)
        
    def on_created(self, event):
        # Acquire the lock and set the flag
        with locks['file_created']:
            flags['file_created'] = True
        # Determine and print system message
        message = None
        new_dir = event.src_path.split('\\')[-1]
        num_created = sum([len(files) for r, d, files in os.walk(new_dir)])
        if num_created <= 1:
            message = f"{new_dir} has been created."
            print(message)
        else:
            message = f"{num_created} files have been created."
            print(message)
        message_queue.put(message)


def monitor_thread(folder_path):
    """Monitor the folder_path and check if there're any files created.

    Args:
        folder_path (str): The path to the folder you want to monitor
    """
                
    event_handler = MyHandler(folder_path)
    observer = Observer()
    observer.schedule(event_handler, path=folder_path, recursive=False)
    observer.start()

    print('Start monitor')
    while True:
        with locks['end']:
            end_flag = flags['end']
        time.sleep(SLEEP_DUR)     # Sleep to avoid starvation
        if end_flag:
            print(f"Stop monitoring {folder_path}.")
            break

if __name__ == "__main__":
    folder_path = "."
    folder_path = os.path.abspath(folder_path)
    # Create file_monitor thread
    file_monitor_thread = threading.Thread(target=monitor_thread, args=(folder_path,))
    # Create display_pet thread
    display_pet_thread = threading.Thread(target=display_pet)
    # Create display_text thread
    display_message_thread = threading.Thread(target=display_message)
    # Create keyboard_sense thread
    keyboard_sense_thread = threading.Thread(target=keyboard_sense)
    # Create audio_mode thread
    audio_mode_thread = threading.Thread(target=audio_mode)
    
    # Start threads
    file_monitor_thread.start()
    display_pet_thread.start()
    display_message_thread.start()
    keyboard_sense_thread.start()
    audio_mode_thread.start()
    
    print('----------------------------')
    print('----------------------------')
    # Wait until threads end
    file_monitor_thread.join()
    display_pet_thread.join()
    display_message_thread.join()
    keyboard_sense_thread.join()
    audio_mode_thread.join()
    
    print("Threads terminated successfully!")
    sys.exit(0)
