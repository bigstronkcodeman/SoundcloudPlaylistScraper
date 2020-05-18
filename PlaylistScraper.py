import os
import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
import requests as rq
import re
import json
import threading
from PIL import Image, ImageTk
from functools import partial

CLIENT_ID = "2412b70da476791567d496f0f3c26b88"
APPENDUM = "?client_id=" + CLIENT_ID

class GUI:
    def __init__(self, beginFunc):
        self.w = tk.Tk()
        self.w.title("Download Ur Music")
        self.init_widgets(beginFunc)

    def init_widgets(self, beginFunc):
        tk.Label(self.w, text="Enter filepath to save your music to: ").grid(row=0)
        tk.Label(self.w, text="Enter url to extract songs from: ").grid(row=1)

        self.folder_path_entry = tk.Entry(self.w)
        self.folder_path_entry.grid(row=0, column=1)
        self.url_path_entry = tk.Entry(self.w)
        self.url_path_entry.grid(row=1, column=1)

        self.img = ImageTk.PhotoImage(Image.open("folder.png").resize((15, 15), Image.ANTIALIAS))
        self.folder_button = tk.Button(self.w, image=self.img, height=20, width=20, command=self.fileDialogButton).grid(row=0, column=2, padx=10)
        self.start_button = tk.Button(self.w, text="BEGIN", command=partial(beginFunc, self.folder_path_entry, self.url_path_entry)).grid(row=2)

    def fileDialogButton(self):
        save_file_directory = tkinter.filedialog.askdirectory()
        self.folder_path_entry.insert(0, save_file_directory)


def extractValidUrl(url):
    rgx = re.search('^(http://|https://|)soundcloud.com/\w+', url)
    if rgx is not None:
        return rgx.group()
    return None

def request_api_data_json(url):
    r = rq.get(url)
    return json.loads(r.text)

def download_api_mp3(url, path):
    r = rq.get(url, stream=True)
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return

def playlist_download_thread(folder_path, url_path, permalink):
    playlists_url = "https://api.soundcloud.com/users/{}/playlists.json{}".format(permalink, APPENDUM)
    playlist_json_list = request_api_data_json(playlists_url)
    for playlist in playlist_json_list:
        playlist_permalink = playlist["permalink"]
        for track in playlist["tracks"]:
            track_path = folder_path + "/" + playlist_permalink
            if not os.path.isdir(track_path):
                os.makedirs(track_path)
            if track["streamable"]:
                print("Downloading " + track["title"] + " by " + track["user"]["username"] + " in playlist " + playlist["title"] + "...")
                download_api_mp3(track["stream_url"] + APPENDUM, track_path + "/" + track["permalink"] + ".mp3")
                print("done.")
    print("All playlists downloaded.")
    return

def start(folder_path_entry, url_path_entry):
    folder_path = folder_path_entry.get() if os.path.isdir(folder_path_entry.get()) else None
    url_path = extractValidUrl(url_path_entry.get())

    if folder_path and url_path:
        permalink = url_path.split("/")[-1]
        threading.Thread(target=playlist_download_thread, args=(folder_path, url_path, permalink)).start()
    else:
        tk.messagebox.showwarning(title="Incomplete user fields", message="Please fill out both fields correctly.")
        return

def main(start):
    gui = GUI(start)
    gui.w.mainloop()

if __name__ == "__main__":
    main(start)
