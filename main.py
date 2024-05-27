import threading
from queue import Queue
from FileServerLib import FileServerLib
import os
from watchdog.observers import Observer     # Ref: https://stackoverflow.com/questions/57840072/how-to-check-for-new-files-in-a-folder-in-python
from watchdog.events import FileSystemEventHandler
import signal

locks = {'file_created':threading.Lock(), 'file_deleted':threading.Lock(), 'end':threading.Lock(), 'falling':threading.Lock()}
flags = {'file_created':False, 'file_deleted':False, 'end':False, 'falling':False}
message_queue = Queue()

# Define a signal handler that handle ctrl+c signal
def end(signum, frame):
    locks['end'].acquire()
    flags['end'] = True
    locks['end'].release()
    print("Ending process...")
# SIGINT means ctrl+c in linux
signal.signal(signal.SIGINT, end)

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
        message =  message_queue.get(timeout=5)
        show_message(message)
        print(message)
        message_queue.task_done()

if __name__ == "__main__":
    folder_path = "."
    folder_path = os.path.abspath(folder_path)
    # Create file_monitor thread
    file_monitor_thread = threading.Thread(target=FileServerLib.monitor_thread, args=(folder_path, locks, flags, message_queue,))
    # Create display_pet thread
    display_pet_thread = threading.Thread(target=display_pet)
    # Create display_text thread
    display_message_thread = threading.Thread(target=display_message)
    
    # Wait until threads end
    file_monitor_thread.join()
    display_pet_thread.join()
    display_message_thread.join()
    print("Process terminated successfully!")