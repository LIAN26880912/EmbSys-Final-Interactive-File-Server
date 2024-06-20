from watchdog.observers import Observer     # Ref: https://stackoverflow.com/questions/57840072/how-to-check-for-new-files-in-a-folder-in-python
from watchdog.events import FileSystemEvent, FileSystemEventHandler
import os
import psutil       # Ref: https://stackoverflow.com/questions/16808721/check-network-connection-from-an-ip-address-with-python
import time        

def get_remote_ips():
    """Get all the remote IPs to the host currently

    Returns:
        remote_ips (set): A set of remote IPs (empty if no connections)
    """
    remote_ips = set()
    connections = psutil.net_connections(kind='inet4')
    for connection in connections:
        addr = connection.raddr
        if len(addr) != 0:
            remote_ips.add(addr.ip)
        
    return remote_ips

def check_no_connections():
    """Check if there are any connections to the host.

    Returns:
        bool: True if no connections.
    """
    remote_ips = get_remote_ips()
    return len(remote_ips) == 0

def monitor(folder_path):
    """Monitor the folder_path and check if there're any files created.

    Args:
        folder_path (str): The path to the folder you want to monitor
    """
    event_handler = MyHandler(folder_path)
    observer = Observer()
    observer.schedule(event_handler, path=folder_path, recursive=False)
    observer.start()

    while True:
        try:
            pass
        except KeyboardInterrupt:
            observer.stop()
            
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
        DELTA_TIME = 2
        if not event.is_directory and time.time()-self.last_modified > DELTA_TIME:
            self.message_queue.put(f"File modified: {event.src_path}")
            # print(f"File modified: {event.src_path}")

if __name__ == "__main__":
    
    current_remote_ips = get_remote_ips()
    print(current_remote_ips)
    print(check_no_connections())
    
    folder_path = 'smb://192.168.50.139'
    folder_path = os.path.abspath(folder_path)
    print(f"------------------- Start monitoring {folder_path} -------------------")
    try:        # Use signal handler for simplicity. (but I just don't wanna)
        monitor(folder_path)
    except KeyboardInterrupt:
        pass
    print(f"------------------- End monitoring {folder_path} -------------------")
