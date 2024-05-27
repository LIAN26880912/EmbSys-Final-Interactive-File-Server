import threading
from queue import Queue, Empty
from FileServerLib import FileServerLib
import os
from watchdog.observers import Observer     # Ref: https://stackoverflow.com/questions/57840072/how-to-check-for-new-files-in-a-folder-in-python
from watchdog.events import FileSystemEventHandler
import signal
from Audio import Audio
import keyboard

locks = {'file_created':threading.Lock(), 'file_deleted':threading.Lock(), 'end':threading.Lock(), 'falling':threading.Lock(), 'music_stop':threading.Lock()}
flags = {'file_created':False, 'file_deleted':False, 'end':False, 'falling':False, 'music_stop':False}
message_queue = Queue()
music_semaphore = threading.Semaphore(0)
TIME_OUT = 1

# Define a signal handler that handle ctrl+c signal
def end(signum, frame):
    locks['end'].acquire()
    flags['end'] = True
    flags['music_stop'] = True
    locks['end'].release()
    print("Ending process...")
# SIGINT means ctrl+c in linux
signal.signal(signal.SIGINT, end)

# Define a signal handler that handle start music button
def music_start(signum, frame):
    print("Starting music mode...")
    music_semaphore.release()
# SIGUSR1 means a user defined signal in linux
signal.signal(signal.SIGUSR1, music_start)

# Define a signal handler that handle music button
def music_stop(signum, frame):
    print("Terminating music mode...")
    locks['music_stop'].acquire()
    flags['music_stop'] = True
    locks['music_stop'].release()
# SIGUSR2 means another user defined signal in linux
signal.signal(signal.SIGUSR2, music_stop)

# Just for safe, I wrote a function works with keyboard instead of signal
def keyboard_sense():
    music_begin = 'y'
    music_end = 't'
    interrupt = 'z'
    while True:
        # Break or not
        locks['end'].acquire()
        end_flag = flags['end']
        locks['end'].release()
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

def display_pet():
    while True:
        # Break or not
        locks['end'].acquire()
        end_flag = flags['end']
        locks['end'].release()
        if end_flag:
            print("End displaying pet.")
            animation_end()
            break
        # Sleep or not
        if FileServerLib.check_no_connections():
            animation_sleeping()
            continue
        # Falling or not
        locks['falling'].acquire()
        falling_flag = flags['falling']
        locks['falling'].release()
        if falling_flag:
            animation_falling()
            continue
        # File created or not
        locks['file_created'].acquire()
        file_created_flag = flags['file_created']
        locks['file_created'].release()
        if file_created_flag:
            animation_file_created()
        # File deleted or not
        locks['file_deleted'].acquire()
        file_deleted_flag = flags['file_deleted']
        locks['file_deleted'].release()
        if file_deleted_flag:
            animation_file_deleted() 
        animation_waiting()
        
def display_message():
    while True:
        # Break or not
        locks['end'].acquire()
        end_flag = flags['end']
        locks['end'].release()
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

        

if __name__ == "__main__":
    folder_path = "."
    folder_path = os.path.abspath(folder_path)
    # Create file_monitor thread
    file_monitor_thread = threading.Thread(target=FileServerLib.monitor_thread, args=(folder_path, locks, flags, message_queue,))
    # Create display_pet thread
    display_pet_thread = threading.Thread(target=display_pet)
    # Create display_text thread
    display_message_thread = threading.Thread(target=display_message)
    # Create keyboard_sense thread
    keyboard_sense_thread = threading.Thread(target=keyboard_sense)
    # Create audio_mode thread
    audio_mode_thread = threading.Thread(target=Audio.audio_mode, args=(music_semaphore, locks, flags, message_queue,))
    
    # Wait until threads end
    file_monitor_thread.join()
    display_pet_thread.join()
    display_message_thread.join()
    keyboard_sense_thread.join()
    audio_mode_thread.join()
    
    print("Process terminated successfully!")
