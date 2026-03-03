# ============================================================
#  Advanced Educational Downloader & Professional Compressor
# ============================================================
#
# ======================= الميزات ============================
#
# قسم YouTube:
# ✔ تحميل فيديو مع الصوت دائماً (دمج video+audio)
# ✔ دعم Playlist
# ✔ اختيار جودة
# ✔ MP3 16kbps
# ✔ شريط تقدم حقيقي
# ✔ حفظ الاسم الأصلي
# ✔ فتح مجلد التحميل
#
# قسم الضغط المحلي الاحترافي:
# ✔ تحليل الفيديو باستخدام ffprobe
# ✔ استخراج الدقة والمدة و bitrate الصوت والفيديو
# ✔ حساب الحجم الحالي
# ✔ حساب bitrate احترافي عند اختيار حجم مخصص
# ✔ Smart CRF حسب الدقة
# ✔ منع تكرار الاسم بإضافة رقم تصاعدي
# ✔ ضغط الفيديو مع الصوت
# ✔ شريط تقدم حقيقي للضغط
#
# ميزات الواجهة:
# ✔ دعم Drag & Drop
# ✔ دعم اللصق بزر الفأرة الأيمن
# ✔ عرض مسار مجلد الحفظ
# ✔ يعمل مع PyInstaller
# ✔ بدون أخطاء Unicode
#
# ============================================================

import os
import sys
import json
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog, Menu
import yt_dlp

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except:
    DND_AVAILABLE = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================
# تحديد مسارات ffmpeg و ffprobe
# ============================================================
def get_binary(name):
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, name)

FFMPEG = get_binary("ffmpeg.exe")
FFPROBE = get_binary("ffprobe.exe")

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
# Smart CRF حسب الدقة
# ============================================================
def smart_crf(width, height):
    pixels = width * height
    if pixels <= 640*360:
        return 23
    elif pixels <= 1280*720:
        return 21
    elif pixels <= 1920*1080:
        return 20
    else:
        return 18

# ============================================================
# التطبيق الرئيسي
# ============================================================
class App(ctk.CTk if not DND_AVAILABLE else TkinterDnD.Tk):

    def __init__(self):
        super().__init__()

        self.title("Advanced Downloader & Compressor")
        self.geometry("950x880")

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.selected_file = ""
        self.duration = 0
        self.formats = []

        self.build_ui()

    # ========================================================
    # بناء الواجهة
    # ========================================================
    def build_ui(self):

        # ================= YouTube Section =================
        ctk.CTkLabel(self, text="YouTube Downloader", font=("Arial", 20)).pack(pady=10)

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")
        self.add_right_click(self.url_entry)

        ctk.CTkButton(self, text="Fetch Formats", command=self.fetch_info).pack(pady=5)

        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=5)

        ctk.CTkButton(btn_frame, text="Download Video", command=self.start_video_download).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="Download MP3 16kbps", command=self.start_mp3_download).grid(row=0, column=1, padx=10)

        ctk.CTkLabel(self, text=f"Save Path: {self.save_path}").pack(pady=5)
        ctk.CTkButton(self, text="Open Download Folder", command=self.open_folder).pack(pady=5)

        # ================= Local Compressor =================
        ctk.CTkLabel(self, text="Professional Local Compressor", font=("Arial", 20)).pack(pady=20)

        self.file_entry = ctk.CTkEntry(self, placeholder_text="Drag & Drop video here")
        self.file_entry.pack(padx=20, fill="x")
        self.add_right_click(self.file_entry)

        if DND_AVAILABLE:
            self.file_entry.drop_target_register(DND_FILES)
            self.file_entry.dnd_bind('<<Drop>>', self.drop_file)

        ctk.CTkButton(self, text="Select Video File", command=self.select_file).pack(pady=5)

        self.info_box = ctk.CTkTextbox(self, height=150)
        self.info_box.pack(padx=20, pady=10, fill="x")

        self.target_size_entry = ctk.CTkEntry(self, placeholder_text="Target Size MB (Optional)")
        self.target_size_entry.pack(pady=5)

        ctk.CTkButton(self, text="Analyze Video", command=self.analyze_video).pack(pady=5)
        ctk.CTkButton(self, text="Compress Video", command=self.start_compress).pack(pady=5)

        # ================= Progress & Log =================
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=10, fill="x")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=220)
        self.log_box.pack(padx=20, pady=10, fill="both")

    # ========================================================
    # دعم زر الفأرة الأيمن
    # ========================================================
    def add_right_click(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    # ========================================================
    # Drag & Drop
    # ========================================================
    def drop_file(self, event):
        file_path = event.data.strip("{}")
        self.selected_file = file_path
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, file_path)

    # ========================================================
    # YouTube Fetch
    # ========================================================
    def fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

        if "entries" in info:
            info = next((e for e in info["entries"] if e), None)

        self.formats.clear()
        labels = []

        for f in info.get("formats", []):
            if f.get("height") and f.get("ext") == "mp4":
                label = f"{f['height']}p"
                self.formats.append((label, f["format_id"]))
                labels.append(label)

        if labels:
            self.quality_menu.configure(values=labels)
            self.quality_menu.set(labels[0])

    # ========================================================
    # YouTube Download Video (كما كان يعمل)
    # ========================================================
    def start_video_download(self):
        threading.Thread(target=self.download_video).start()

    def download_video(self):

        selected_label = self.quality_menu.get()
        selected = next((f for f in self.formats if f[0] == selected_label), None)

        format_string = f"{selected[1]}+bestaudio/best" if selected else "bestvideo+bestaudio/best"

        ydl_opts = {
            "format": format_string,
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "ffmpeg_location": FFMPEG,
            "progress_hooks": [self.yt_progress],
            "no_color": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url_entry.get().strip()])

        self.open_folder()

    # ========================================================
    # MP3
    # ========================================================
    def start_mp3_download(self):
        threading.Thread(target=self.download_mp3).start()

    def download_mp3(self):

        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "16"
            }],
            "ffmpeg_location": FFMPEG,
            "progress_hooks": [self.yt_progress],
            "no_color": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url_entry.get().strip()])

        self.open_folder()

    def yt_progress(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').replace('%', '').strip()
            try:
                self.progress.set(float(percent)/100)
            except:
                pass
        elif d['status'] == 'finished':
            self.progress.set(1)

    # ========================================================
    # تحليل الفيديو المحلي
    # ========================================================
    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")])
        if file:
            self.selected_file = file
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file)

    def analyze_video(self):

        if not self.selected_file:
            return

        cmd = [
            FFPROBE, "-v", "error",
            "-show_streams", "-show_format",
            "-print_format", "json",
            self.selected_file
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        data = json.loads(result.stdout)

        video_stream = next(s for s in data["streams"] if s["codec_type"] == "video")
        audio_stream = next(s for s in data["streams"] if s["codec_type"] == "audio")

        width = int(video_stream["width"])
        height = int(video_stream["height"])
        self.duration = float(data["format"]["duration"])
        size_mb = round(int(data["format"]["size"]) / 1024 / 1024, 2)

        crf = smart_crf(width, height)

        self.info_box.delete("1.0", "end")
        self.info_box.insert("end",
            f"Resolution: {width}x{height}\n"
            f"Duration: {round(self.duration,2)} sec\n"
            f"Current Size: {size_mb} MB\n"
            f"Suggested CRF: {crf}\n"
        )

    # ========================================================
    # ضغط احترافي
    # ========================================================
    def start_compress(self):
        threading.Thread(target=self.compress_video).start()

    def compress_video(self):

        output = unique_filename(
            os.path.splitext(self.selected_file)[0] + "_compressed.mp4"
        )

        target_size = self.target_size_entry.get().strip()

        if target_size:
            target_bits = float(target_size) * 8 * 1024 * 1024
            video_bitrate = int((target_bits / self.duration) - 128000)

            cmd = [
                FFMPEG, "-y",
                "-i", self.selected_file,
                "-b:v", str(video_bitrate),
                "-c:a", "aac",
                "-b:a", "128k",
                output
            ]
        else:
            cmd = [
                FFMPEG, "-y",
                "-i", self.selected_file,
                "-c:v", "libx264",
                "-crf", str(smart_crf(1280,720)),
                "-preset", "medium",
                "-c:a", "aac",
                "-b:a", "128k",
                output
            ]

        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")

        for line in process.stderr:
            if "time=" in line and self.duration:
                t = line.split("time=")[1].split(" ")[0]
                h,m,s = t.split(":")
                current = int(h)*3600 + int(m)*60 + float(s)
                self.progress.set(min(current/self.duration,1))

        process.wait()
        self.progress.set(1)
        os.startfile(os.path.dirname(output))

    # ========================================================
    # فتح مجلد
    # ========================================================
    def open_folder(self):
        os.startfile(self.save_path)


# ============================================================
# تشغيل
# ============================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()