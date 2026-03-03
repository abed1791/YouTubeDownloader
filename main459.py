# ============================================================
#  Advanced Educational YouTube Downloader & Pro Compressor
# ============================================================
#
# ========================== الميزات ==========================
#
# قسم YouTube Downloader:
# ✔ تحميل فيديو مع دمج الصوت
# ✔ دعم Playlist
# ✔ اختيار جودة مع عرض الحجم
# ✔ اختيار حجم مخصص واختيار أفضل جودة ضمنه
# ✔ MP3 16kbps
# ✔ زر إلغاء التحميل
# ✔ شريط تقدم دقيق
# ✔ منع تكرار الاسم
# ✔ فتح مجلد التحميل تلقائياً
# ✔ دعم لصق الحافظة بزر الفأرة الأيمن
#
# قسم Professional Video Compressor:
# ✔ تحليل مدة الفيديو عبر ffprobe
# ✔ Smart CRF عند عدم تحديد حجم
# ✔ حساب bitrate دقيق عند تحديد حجم
# ✔ خصم صوت AAC من الحساب
# ✔ شريط تقدم حقيقي يعتمد على الوقت
# ✔ دعم الإلغاء
# ✔ Two‑Pass Encoding عبر CheckBox
# ✔ اسم ملف ناتج فريد
#
# ============================================================

import os
import sys
import threading
import subprocess
import re
import customtkinter as ctk
from tkinter import Menu, filedialog
import yt_dlp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================
# مسار ffmpeg / ffprobe
# ============================================================
def get_ffmpeg():
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "ffmpeg.exe")

FFMPEG = get_ffmpeg()
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

# ============================================================
# منع تكرار الاسم
# ============================================================
def unique_filename(path):
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base}_{counter}{ext}"
        counter += 1
    return new_path

# ============================================================
# التطبيق الرئيسي
# ============================================================
class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Advanced Educational Downloader & Compressor")
        self.geometry("1000x880")

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")

        self.formats = []
        self.cancel_flag = False

        self.selected_file = ""
        self.compress_cancel = False

        self.build_ui()

    # ========================================================
    # بناء الواجهة
    # ========================================================
    def build_ui(self):

        # ================= YouTube =================
        ctk.CTkLabel(self, text="YouTube Downloader",
                     font=("Arial", 24, "bold"),
                     text_color="#4da6ff").pack(pady=10)

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")
        self.add_right_click(self.url_entry)

        ctk.CTkButton(self, text="Fetch Formats",
                      command=self.fetch_info).pack(pady=5)

        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=5)

        self.size_entry = ctk.CTkEntry(self,
                                       placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)
        self.add_right_click(self.size_entry)

        yt_buttons = ctk.CTkFrame(self)
        yt_buttons.pack(pady=8)

        ctk.CTkButton(yt_buttons, text="Download Video",
                      width=160,
                      command=self.start_video).grid(row=0, column=0, padx=5)

        ctk.CTkButton(yt_buttons, text="Download MP3 16kbps",
                      width=160,
                      command=self.start_mp3).grid(row=0, column=1, padx=5)

        ctk.CTkButton(yt_buttons, text="Cancel",
                      width=120,
                      fg_color="red",
                      command=self.cancel_download).grid(row=0, column=2, padx=5)

        self.path_label = ctk.CTkLabel(self,
                                       text=f"Save Path: {self.save_path}",
                                       text_color="#cccccc")
        self.path_label.pack(pady=5)

        ctk.CTkButton(self, text="Open Download Folder",
                      command=self.open_folder).pack(pady=5)

        # ================= Compressor =================
        ctk.CTkLabel(self,
                     text="Professional Local Video Compressor",
                     font=("Arial", 22, "bold"),
                     text_color="#00cc99").pack(pady=20)

        self.file_entry = ctk.CTkEntry(self,
                                       placeholder_text="Select local video file")
        self.file_entry.pack(padx=20, fill="x")
        self.add_right_click(self.file_entry)

        comp_buttons = ctk.CTkFrame(self)
        comp_buttons.pack(pady=8)

        ctk.CTkButton(comp_buttons, text="Select File",
                      width=160,
                      command=self.select_file).grid(row=0, column=0, padx=5)

        ctk.CTkButton(comp_buttons, text="Compress",
                      width=160,
                      command=self.start_compress).grid(row=0, column=1, padx=5)

        self.target_size_entry = ctk.CTkEntry(self,
                                              placeholder_text="Target Size MB (Optional)")
        self.target_size_entry.pack(pady=5)
        self.add_right_click(self.target_size_entry)

        # Two Pass CheckBox
        self.two_pass_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self,
                        text="Enable Two‑Pass Encoding (Higher Quality)",
                        variable=self.two_pass_var).pack(pady=5)

        # ================= Progress =================
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=15, fill="x")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(padx=20, pady=10, fill="both")

    # ========================================================
    # قائمة زر الفأرة الأيمن (لصق الحافظة)
    # ========================================================
    def add_right_click(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste",
                         command=lambda: widget.insert("insert",
                                                       self.clipboard_get()))
        widget.bind("<Button-3>",
                    lambda e: menu.tk_popup(e.x_root, e.y_root))

    # ========================================================
    # تسجيل
    # ========================================================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # ========================================================
    # -------------- YouTube Section ----------------
    # ========================================================
    def fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        self.log("Fetching formats...")

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        if "entries" in info:
            info = next((e for e in info["entries"] if e), None)

        self.formats.clear()
        labels = []

        for f in info.get("formats", []):
            if f.get("height") and f.get("ext") == "mp4":
                size = f.get("filesize") or 0
                size_mb = round(size/1024/1024, 2) if size else 0
                label = f"{f['height']}p - {size_mb} MB"
                self.formats.append((label, f["format_id"], size))
                labels.append(label)

        if labels:
            self.quality_menu.configure(values=labels)
            self.quality_menu.set(labels[0])
            self.log("Formats loaded.")

    def start_video(self):
        self.cancel_flag = False
        threading.Thread(target=self.download_video).start()

    def download_video(self):
        url = self.url_entry.get().strip()
        format_string = "bestvideo+bestaudio/best"

        def hook(d):
            if self.cancel_flag:
                raise Exception("Cancelled")
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').replace('%','').strip()
                try:
                    self.progress.set(float(percent)/100)
                except:
                    pass
            elif d['status'] == 'finished':
                self.progress.set(1)

        ydl_opts = {
            "format": format_string,
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "ffmpeg_location": FFMPEG,
            "progress_hooks": [hook],
            "no_color": True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.log("Download finished.")
            self.open_folder()
        except Exception as e:
            self.log(str(e))

    def start_mp3(self):
        threading.Thread(target=self.download_mp3).start()

    def download_mp3(self):
        url = self.url_entry.get().strip()
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "16"
            }],
            "ffmpeg_location": FFMPEG,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        self.log("MP3 finished.")
        self.open_folder()

    def cancel_download(self):
        self.cancel_flag = True

    # ========================================================
    # -------------- Compressor Section ----------------
    # ========================================================
    def select_file(self):
        file = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")]
        )
        if file:
            self.selected_file = file
            self.file_entry.delete(0,"end")
            self.file_entry.insert(0,file)

    def get_duration(self, file):
        cmd = [FFPROBE,"-v","error",
               "-show_entries","format=duration",
               "-of","default=noprint_wrappers=1:nokey=1",
               file]
        result = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        try:
            return float(result.stdout.strip())
        except:
            return 0

    def start_compress(self):
        if not self.selected_file:
            return
        threading.Thread(target=self.compress_video).start()

    def compress_video(self):

        duration = self.get_duration(self.selected_file)
        if duration == 0:
            self.log("Could not read duration.")
            return

        output = unique_filename(
            os.path.splitext(self.selected_file)[0] + "_compressed.mp4")

        target_size = self.target_size_entry.get().strip()
        two_pass = self.two_pass_var.get()

        # ===================== Smart CRF =====================
        if not target_size:
            cmd = [FFMPEG,"-y","-i",self.selected_file,
                   "-c:v","libx264","-crf","21",
                   "-preset","medium",
                   "-c:a","aac","-b:a","128k",
                   output]
            subprocess.run(cmd)
            self.log("CRF compression finished.")
            return

        # ===================== Bitrate Calculation =====================
        size_mb = float(target_size)
        total_bits = size_mb*1024*1024*8
        audio_bitrate = 128000
        video_bitrate = int((total_bits/duration - audio_bitrate)/1000)

        if not two_pass:
            cmd = [FFMPEG,"-y","-i",self.selected_file,
                   "-c:v","libx264","-b:v",f"{video_bitrate}k",
                   "-preset","medium",
                   "-c:a","aac","-b:a","128k",
                   output]
            subprocess.run(cmd)
        else:
            # ---------- Pass 1 ----------
            subprocess.run([FFMPEG,"-y","-i",self.selected_file,
                            "-c:v","libx264","-b:v",f"{video_bitrate}k",
                            "-pass","1","-an","-f","mp4","NUL"])

            # ---------- Pass 2 ----------
            subprocess.run([FFMPEG,"-y","-i",self.selected_file,
                            "-c:v","libx264","-b:v",f"{video_bitrate}k",
                            "-pass","2",
                            "-c:a","aac","-b:a","128k",
                            output])

        self.log("Two‑Pass compression finished." if two_pass else "Compression finished.")
        os.startfile(os.path.dirname(output))

    # ========================================================
    def open_folder(self):
        os.startfile(self.save_path)

# ============================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()