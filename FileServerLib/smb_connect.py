import os
import time
from smb.SMBConnection import SMBConnection
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define SMB connection parameters
smb_server = "192.168.0.63"
smb_share = "SharePi"
username = "pi"
password = "abc123"
client_machine_name = "Wesley"
mount_point = "/mnt/smb_share"

# Connect to SMB server
def connect_to_smb():
    conn = SMBConnection(username, password, client_machine_name, smb_server, use_ntlm_v2=True)
    assert conn.connect(smb_server, 139)
    return conn

# Mount the SMB share
def mount_smb():
    if not os.path.exists(mount_point):
        os.makedirs(mount_point)
    os.system(f"sudo mount.cifs //{smb_server}/{smb_share} {mount_point} -o user={username},password={password}")

# Unmount the SMB share
def unmount_smb():
    os.system(f"sudo umount {mount_point}")

# Event handler class for watchdog
class SMBEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        # self.path = path
        self.last_modified = time.time()    # To avoid on_modified ran twice


    def on_created(self, event):
        if not event.is_directory:
            print(f"File created: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"File deleted: {event.src_path}")

    def on_modified(self, event):
        cur_time = time.time()
        if not event.is_directory and cur_time-self.last_modified > 0.5:
            self.last_modified = cur_time
            print(f"File modified: {event.src_path}")

    def on_moved(self, event):
        if not event.is_directory:
            print(f"File moved: {event.src_path}")

# Main function
def main():
    # Connect to SMB server
    conn = connect_to_smb()
    print("Connected to SMB server")

    # Mount the SMB share
    mount_smb()
    print(f"Mounted SMB share at {mount_point}")

    # Set up watchdog observer
    event_handler = SMBEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=mount_point, recursive=True)
    observer.start()
	
    # Just for testing
    time.sleep(0.5)
    with open(mount_point+'/test.txt', 'w') as f:
        f.write('good')
    print('File writed')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    # Unmount the SMB share
    unmount_smb()
    print(f"Unmounted SMB share from {mount_point}")

if __name__ == "__main__":
    main()