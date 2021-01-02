import os
import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
import requests as rq
import shutil
import re
import json
import threading
from PIL import Image, ImageTk
from functools import partial
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TPE1, error

CLIENT_ID = "2412b70da476791567d496f0f3c26b88"
APPENDUM = "?client_id=" + CLIENT_ID

class GUI:
    def __init__(self, beginFunc):
        self.w = tk.Tk()
        self.w.title("Download Your Music")
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

def rem_bad_chars(fname):
    for c in [ "<", ">", ":", "\"", "/", "\\", "|", "?", "*" ]:
        fname = fname.replace(c, " ")
    return fname

def extractValidUrl(url):
    rgx = re.search('^(http://|https://|)soundcloud.com/\w+', url)
    if rgx is not None:
        return rgx.group()
    return None

def request_api_data_json(url):
    r = rq.get(url)
    return json.loads(r.text)

def download_api_mp3(audio_url, art_url, artist, path):
    r = rq.get(audio_url, stream=True)
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    mp3 = MP3(path, ID3=ID3)
    try:
        mp3.add_tags()
    except error:
        pass
    if art_url is not None:
        art_url = "t500x500".join(art_url.rsplit("large", 1)) # get high resolution artwork instead of the shitty low res one sc wants you to have
        img_response = rq.get(art_url, stream=True)
        with open("temp.jpg", "wb") as f:
            shutil.copyfileobj(img_response.raw, f)
        del img_response
        mp3.tags.add(APIC(mime="image/jpeg", type=3, desc=u"Cover", data=open("temp.jpg", "rb").read()))
    mp3.tags.add(TPE1(encoding=3, text=f"{artist}"))
    mp3.save()
    return

def playlist_download_thread(folder_path, url_path, permalink):
    profile_url = f"https://api.soundcloud.com/users/{permalink}{APPENDUM}"
    profile_id = request_api_data_json(profile_url)["id"]
    playlists_url = f"https://api.soundcloud.com/users/{profile_id}/playlists.json{APPENDUM}"
    playlist_json_list = request_api_data_json(playlists_url)
    for playlist in playlist_json_list:
        playlist_title = rem_bad_chars(playlist["title"])
        for track in playlist["tracks"]:
            track_path = folder_path + "/" + playlist_title
            if not os.path.isdir(track_path):
                os.makedirs(track_path)
            if track["streamable"]:
                print(f"Downloading {track['title']} by {track['user']['username']} in playlist {playlist['title']}...")
                track_name = rem_bad_chars(track["title"])
                download_api_mp3(f"{track['stream_url']}{APPENDUM}", track["artwork_url"], track["user"]["username"], f"{track_path}/{track_name}.mp3")
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
