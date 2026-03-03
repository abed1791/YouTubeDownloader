# ============================================================
# Advanced Downloader & Compressor - Fixed Version
# ============================================================

import os, sys, json, threading, subprocess
import customtkinter as ctk
from tkinter import filedialog, Menu
import yt_dlp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def get_binary(name):
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)

FFMPEG = get_binary("ffmpeg.exe")
FFPROBE = get_binary("ffprobe.exe")

def unique_filename(path):
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1
    return new_path

def smart_crf(width, height):
    pixels = width*height
    if pixels <= 640*360: return 23
    elif pixels <= 1280*720: return 21
    elif pixels <= 1920*1080: return 20
    else: return 18

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Downloader & Compressor")
        self.geometry("950x900")
        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.selected_file = ""
        self.duration = 0
        self.formats = []
        self.build_ui()

    def build_ui(self):
        # YouTube Section
        yt_frame = ctk.CTkFrame(self, corner_radius=10)
        yt_frame.pack(padx=20, pady=15, fill="x")
        ctk.CTkLabel(yt_frame, text="YouTube Downloader", font=("Arial",20,"bold"), text_color="#4da6ff").pack(pady=10)
        self.url_entry = ctk.CTkEntry(yt_frame, placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")
        self.add_right_click(self.url_entry)
        self.quality_menu = ctk.CTkOptionMenu(yt_frame, values=["Select Quality"])
        self.quality_menu.pack(pady=8)
        yt_buttons = ctk.CTkFrame(yt_frame)
        yt_buttons.pack(pady=10)
        ctk.CTkButton(yt_buttons,text="Fetch Formats",width=140,command=self.fetch_info).grid(row=0,column=0,padx=8)
        ctk.CTkButton(yt_buttons,text="Download Video",width=160,command=self.start_video_download).grid(row=0,column=1,padx=8)
        ctk.CTkButton(yt_buttons,text="Download MP3 16kbps",width=160,command=self.start_mp3_download).grid(row=0,column=2,padx=8)
        ctk.CTkLabel(yt_frame, text=f"Save Path: {self.save_path}", text_color="#cccccc").pack(pady=5)
        ctk.CTkButton(yt_frame,text="Open Download Folder",command=self.open_folder).pack(pady=5)

        # Local Compressor
        comp_frame = ctk.CTkFrame(self, corner_radius=10)
        comp_frame.pack(padx=20,pady=20,fill="x")
        ctk.CTkLabel(comp_frame,text="Local Video Compressor",font=("Arial",20,"bold"),text_color="#66ff99").pack(pady=10)
        self.file_entry = ctk.CTkEntry(comp_frame, placeholder_text="Video File Path")
        self.file_entry.pack(padx=20, fill="x")
        self.add_right_click(self.file_entry)
        self.info_box = ctk.CTkTextbox(comp_frame,height=150)
        self.info_box.pack(padx=20,pady=10,fill="x")
        self.target_size_entry = ctk.CTkEntry(comp_frame,placeholder_text="Target Size MB (Optional)")
        self.target_size_entry.pack(pady=5)
        comp_buttons = ctk.CTkFrame(comp_frame)
        comp_buttons.pack(pady=10)
        ctk.CTkButton(comp_buttons,text="Select File",width=160,command=self.select_file).grid(row=0,column=0,padx=8)
        ctk.CTkButton(comp_buttons,text="Analyze Video",width=150,command=self.analyze_video).grid(row=0,column=1,padx=8)
        ctk.CTkButton(comp_buttons,text="Compress Video",width=150,command=self.start_compress).grid(row=0,column=2,padx=8)

        # Progress & Log
        ctk.CTkLabel(self,text="Operation Progress",font=("Arial",16,"bold"),text_color="#ffcc66").pack(pady=10)
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20,pady=5,fill="x")
        self.progress.set(0)
        self.log_box = ctk.CTkTextbox(self,height=220)
        self.log_box.pack(padx=20,pady=10,fill="both")

    def add_right_click(self,widget):
        menu = Menu(widget,tearoff=0)
        menu.add_command(label="Paste",command=lambda:widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root,e.y_root))

    # ---------------- YouTube ----------------
    def fetch_info(self):
        url = self.url_entry.get().strip()
        if not url: return
        with yt_dlp.YoutubeDL({"quiet":True}) as ydl:
            info = ydl.extract_info(url,download=False)
        if "entries" in info:
            info = next((e for e in info["entries"] if e), None)
        self.formats.clear()
        labels=[]
        for f in info.get("formats",[]):
            if f.get("height") and f.get("ext")=="mp4":
                label=f"{f['height']}p"
                self.formats.append((label,f["format_id"]))
                labels.append(label)
        if labels:
            self.quality_menu.configure(values=labels)
            self.quality_menu.set(labels[0])

    def start_video_download(self):
        threading.Thread(target=self.download_video,daemon=True).start()
    def download_video(self):
        selected_label=self.quality_menu.get()
        selected=next((f for f in self.formats if f[0]==selected_label),None)
        format_string=f"{selected[1]}+bestaudio/best" if selected else "bestvideo+bestaudio/best"
        ydl_opts={
            "format":format_string,
            "outtmpl":os.path.join(self.save_path,"%(title)s.%(ext)s"),
            "merge_output_format":"mp4",
            "ffmpeg_location":FFMPEG,
            "progress_hooks":[self.yt_progress],
            "no_color":True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url_entry.get().strip()])
        self.open_folder()

    def start_mp3_download(self):
        threading.Thread(target=self.download_mp3,daemon=True).start()
    def download_mp3(self):
        ydl_opts={
            "format":"bestaudio",
            "outtmpl":os.path.join(self.save_path,"%(title)s.%(ext)s"),
            "postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"16"}],
            "ffmpeg_location":FFMPEG,
            "progress_hooks":[self.yt_progress],
            "no_color":True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url_entry.get().strip()])
        self.open_folder()

    def yt_progress(self,d):
        if d['status']=="downloading":
            percent=d.get("_percent_str","0%").replace("%","").strip()
            try:self.progress.set(float(percent)/100)
            except:pass
        elif d['status']=="finished":
            self.progress.set(1)

    # ---------------- Local Video ----------------
    def select_file(self):
        file=filedialog.askopenfilename(filetypes=[("Video Files","*.mp4 *.mkv *.avi *.mov")])
        if file:
            self.selected_file=file
            self.file_entry.delete(0,"end")
            self.file_entry.insert(0,file)

    def analyze_video(self):
        if not self.selected_file: return
        cmd=[FFPROBE,"-v","error","-show_streams","-show_format","-print_format","json",self.selected_file]
        try:
            result=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="ignore")
            data=json.loads(result.stdout)
        except Exception as e:
            self.log_box.insert("end", f"FFprobe Error: {e}\n")
            return
        video_stream=next(s for s in data["streams"] if s["codec_type"]=="video")
        width=int(video_stream["width"])
        height=int(video_stream["height"])
        self.duration=float(data["format"]["duration"])
        size_mb=round(int(data["format"]["size"])/1024/1024,2)
        crf=smart_crf(width,height)
        self.info_box.delete("1.0","end")
        self.info_box.insert("end",
            f"Resolution: {width}x{height}\n"
            f"Duration: {round(self.duration,2)} sec\n"
            f"Current Size: {size_mb} MB\n"
            f"Suggested CRF: {crf}\n"
        )

    def start_compress(self):
        if self.duration==0:
            self.log_box.insert("end","Error: Analyze video first!\n")
            return
        threading.Thread(target=self.compress_video,daemon=True).start()

    def compress_video(self):
        output=unique_filename(os.path.splitext(self.selected_file)[0]+"_compressed.mp4")
        target_size=self.target_size_entry.get().strip()
        if target_size and self.duration>0:
            target_bits=float(target_size)*8*1024*1024
            video_bitrate=int((target_bits/self.duration)-128000)
            cmd=[FFMPEG,"-y","-i",self.selected_file,"-b:v",str(video_bitrate),"-c:a","aac","-b:a","128k",output]
        else:
            cmd=[FFMPEG,"-y","-i",self.selected_file,"-c:v","libx264","-crf",str(smart_crf(1280,720)),"-preset","medium","-c:a","aac","-b:a","128k",output]
        process=subprocess.Popen(cmd,stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="ignore")
        for line in process.stderr:
            if "time=" in line and self.duration:
                t=line.split("time=")[1].split(" ")[0]
                try:
                    h,m,s=t.split(":")
                    current=int(h)*3600+int(m)*60+float(s)
                    self.progress.set(min(current/self.duration,1))
                except: pass
        process.wait()
        self.progress.set(1)
        os.startfile(os.path.dirname(output))

    def open_folder(self):
        os.startfile(self.save_path)

if __name__=="__main__":
    app=App()
    app.mainloop()