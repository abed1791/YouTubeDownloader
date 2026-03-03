# ============================================================
#  Advanced Educational Downloader & Smart Video Compressor
# ============================================================
#
#  الميزات التعليمية الكاملة:
# ------------------------------------------------------------
# ✔ تحميل فيديو يوتيوب مع الصوت دائماً (دمج video + audio)
# ✔ دعم Playlist
# ✔ اختيار جودة أو حجم مخصص
# ✔ MP3 16kbps
# ✔ منع أخطاء ANSI / Unicode
# ✔ يعمل مع PyInstaller (مسار ffmpeg ديناميكي)
# ✔ دعم اللصق بزر الفأرة الأيمن
# ✔ دعم Drag & Drop لملفات الفيديو
# ✔ فتح مجلد الإخراج بعد الانتهاء
# ✔ عند وجود ملف بنفس الاسم → إعادة تسمية تلقائياً برقم تصاعدي
#
# ✔ نظام ضغط احترافي جداً:
#     - تحليل دقة الفيديو تلقائياً
#     - اختيار CRF ذكي حسب الدقة
#     - ضغط أولي باستخدام CRF
#     - إذا تجاوز الحجم المطلوب → إعادة ضغط بمرحلتين 2-Pass Bitrate
#     - احتساب bitrate الفيديو بعد خصم bitrate الصوت
#
# ============================================================

import os
import sys
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

AUDIO_BITRATE = 128000  # 128kbps


# ============================================================
# مسار ffmpeg متوافق مع EXE
# ============================================================
def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "ffmpeg.exe")


# ============================================================
# إعادة تسمية تلقائية عند وجود ملف مشابه
# ============================================================
def get_unique_filename(path):
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
class App(ctk.CTk if not DND_AVAILABLE else TkinterDnD.Tk):

    def __init__(self):
        super().__init__()

        self.title("Advanced Educational Downloader & Smart Compressor")
        self.geometry("900x800")

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.formats = []
        self.selected_file = ""

        self.build_ui()

    # ============================================================
    # واجهة المستخدم
    # ============================================================
    def build_ui(self):

        ctk.CTkLabel(self, text="YouTube Downloader", font=("Arial", 18)).pack(pady=10)

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")

        self.add_right_click_menu(self.url_entry)

        ctk.CTkButton(self, text="Fetch Formats", command=self.fetch_info).pack(pady=5)

        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=5)

        ctk.CTkButton(self, text="Download Video", command=self.start_video_download).pack(pady=5)
        ctk.CTkButton(self, text="Download MP3 16kbps", command=self.start_mp3_download).pack(pady=5)

        # -------------------------------------------------------

        ctk.CTkLabel(self, text="Smart Local Video Compressor", font=("Arial", 18)).pack(pady=15)

        self.file_entry = ctk.CTkEntry(self, placeholder_text="Drag & Drop video here")
        self.file_entry.pack(padx=20, fill="x")

        self.add_right_click_menu(self.file_entry)

        if DND_AVAILABLE:
            self.file_entry.drop_target_register(DND_FILES)
            self.file_entry.dnd_bind('<<Drop>>', self.drop_file)

        ctk.CTkButton(self, text="Select Video File", command=self.select_video_file).pack(pady=5)

        self.target_size_entry = ctk.CTkEntry(self, placeholder_text="Target Size MB (Optional)")
        self.target_size_entry.pack(pady=5)

        ctk.CTkButton(self, text="Compress Video", command=self.start_compress).pack(pady=5)

        self.log_box = ctk.CTkTextbox(self, height=250)
        self.log_box.pack(padx=20, pady=10, fill="both")

        ctk.CTkButton(self, text="Open Download Folder", command=self.open_folder).pack(pady=5)

    # ============================================================
    # أدوات مساعدة
    # ============================================================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def open_folder(self):
        os.startfile(self.save_path)

    def add_right_click_menu(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def drop_file(self, event):
        file_path = event.data.strip("{}")
        self.selected_file = file_path
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, file_path)

    # ============================================================
    # تحميل يوتيوب
    # ============================================================
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
            "ffmpeg_location": get_ffmpeg_path(),
            "no_color": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url_entry.get().strip()])

        self.log("Download finished")

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
            "ffmpeg_location": get_ffmpeg_path(),
            "no_color": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url_entry.get().strip()])

        self.log("MP3 finished")

    # ============================================================
    # الضغط الاحترافي الذكي
    # ============================================================
    def select_video_file(self):
        file = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov")])
        if file:
            self.selected_file = file
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file)

    def start_compress(self):
        threading.Thread(target=self.compress_video).start()

    def compress_video(self):

        ffmpeg = get_ffmpeg_path()

        # استخراج معلومات الفيديو
        cmd = [ffmpeg, "-i", self.selected_file]
        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding="utf-8",
            errors="ignore"
        )

        duration_line = next((l for l in result.stderr.split("\n") if "Duration" in l), None)
        resolution_line = next((l for l in result.stderr.split("\n") if "Video:" in l), None)

        time_str = duration_line.split("Duration:")[1].split(",")[0].strip()
        h, m, s = time_str.split(":")
        duration = int(h)*3600 + int(m)*60 + float(s)

        # استخراج الدقة
        import re
        match = re.search(r'(\d{3,4})x(\d{3,4})', resolution_line)
        width = int(match.group(1))
        height = int(match.group(2))

        # اختيار CRF ذكي حسب الدقة
        if height >= 2160:
            crf = 23
        elif height >= 1440:
            crf = 22
        elif height >= 1080:
            crf = 21
        elif height >= 720:
            crf = 20
        else:
            crf = 18

        output = os.path.splitext(self.selected_file)[0] + "_compressed.mp4"
        output = get_unique_filename(output)

        # ضغط أولي باستخدام CRF
        command = [
            ffmpeg,
            "-y",
            "-i", self.selected_file,
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", "128k",
            output
        ]

        subprocess.run(command)

        # إذا حدد المستخدم حجم مستهدف
        if self.target_size_entry.get():
            target_size = float(self.target_size_entry.get())
            final_size_mb = os.path.getsize(output) / (1024 * 1024)

            if final_size_mb > target_size:
                os.remove(output)

                target_bits = target_size * 8 * 1024 * 1024
                video_bitrate = int((target_bits / duration) - AUDIO_BITRATE)

                # ضغط 2-Pass احترافي
                pass1 = [
                    ffmpeg, "-y", "-i", self.selected_file,
                    "-c:v", "libx264",
                    "-b:v", str(video_bitrate),
                    "-pass", "1",
                    "-an",
                    "-f", "mp4",
                    "NUL"
                ]

                pass2 = [
                    ffmpeg, "-y", "-i", self.selected_file,
                    "-c:v", "libx264",
                    "-b:v", str(video_bitrate),
                    "-pass", "2",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    output
                ]

                subprocess.run(pass1)
                subprocess.run(pass2)

        self.log("Compression finished")
        os.startfile(os.path.dirname(output))


# ============================================================
# تشغيل التطبيق
# ============================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()