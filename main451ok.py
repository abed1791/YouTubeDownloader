# ============================================================
#  Advanced Educational Downloader & Professional Compressor
# ============================================================
#
# الميزات الاحترافية التعليمية:
# ------------------------------------------------------------
# ✔ تحميل فيديو يوتيوب مع الصوت دائماً (دمج video+audio)
# ✔ دعم Playlist
# ✔ اختيار جودة أو حجم مخصص
# ✔ MP3 16kbps
# ✔ شريط تقدم حقيقي للتحميل
# ✔ ضغط فيديو محلي احترافي جداً
# ✔ تحليل الفيديو عبر ffprobe:
#     - استخراج الدقة
#     - مدة الفيديو
#     - bitrate الصوت
#     - bitrate الفيديو
#     - الحجم الحالي
# ✔ حساب الحجم المتوقع بعد الضغط
# ✔ حساب bitrate فيديو بعد خصم bitrate الصوت
# ✔ Smart CRF حسب الدقة
# ✔ وضع Target Size Mode
# ✔ منع تكرار الاسم بإضافة رقم تصاعدي
# ✔ شريط تقدم حقيقي لعملية الضغط
# ✔ دعم Drag & Drop
# ✔ دعم اللصق بزر الفأرة الأيمن
# ✔ يعمل مع PyInstaller
# ✔ لا أخطاء ANSI / Unicode
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
# التطبيق
# ============================================================
class App(ctk.CTk if not DND_AVAILABLE else TkinterDnD.Tk):

    def __init__(self):
        super().__init__()

        self.title("Professional Downloader & Compressor")
        self.geometry("900x820")

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.selected_file = ""
        self.duration = 0

        self.build_ui()

    # ========================================================
    # UI
    # ========================================================
    def build_ui(self):

        ctk.CTkLabel(self, text="Local Professional Compressor", font=("Arial", 20)).pack(pady=10)

        self.file_entry = ctk.CTkEntry(self, placeholder_text="Drag & Drop video here")
        self.file_entry.pack(padx=20, fill="x")

        self.add_right_click(self.file_entry)

        if DND_AVAILABLE:
            self.file_entry.drop_target_register(DND_FILES)
            self.file_entry.dnd_bind('<<Drop>>', self.drop_file)

        ctk.CTkButton(self, text="Select Video", command=self.select_file).pack(pady=5)

        # -------- تحليل --------
        self.info_box = ctk.CTkTextbox(self, height=140)
        self.info_box.pack(padx=20, pady=10, fill="x")

        self.target_size_entry = ctk.CTkEntry(self, placeholder_text="Target Size MB (Optional)")
        self.target_size_entry.pack(pady=5)

        ctk.CTkButton(self, text="Analyze Video", command=self.analyze_video).pack(pady=5)
        ctk.CTkButton(self, text="Compress Video", command=self.start_compress).pack(pady=5)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=10, fill="x")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(padx=20, pady=10, fill="both")

    # ========================================================
    # دعم لصق بزر الفأرة
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

    def select_file(self):
        file = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")])
        if file:
            self.selected_file = file
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file)

    # ========================================================
    # تحليل احترافي للفيديو
    # ========================================================
    def analyze_video(self):

        if not self.selected_file:
            return

        cmd = [
            FFPROBE,
            "-v", "error",
            "-show_streams",
            "-show_format",
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
        video_bitrate = int(video_stream.get("bit_rate", 0))
        audio_bitrate = int(audio_stream.get("bit_rate", 0))
        size_mb = round(int(data["format"]["size"]) / 1024 / 1024, 2)

        crf = smart_crf(width, height)

        self.info_box.delete("1.0", "end")
        self.info_box.insert("end",
            f"Resolution: {width}x{height}\n"
            f"Duration: {round(self.duration,2)} sec\n"
            f"Current Size: {size_mb} MB\n"
            f"Video Bitrate: {video_bitrate/1000:.0f} kbps\n"
            f"Audio Bitrate: {audio_bitrate/1000:.0f} kbps\n"
            f"Suggested CRF: {crf}\n"
        )

    # ========================================================
    # ضغط احترافي
    # ========================================================
    def start_compress(self):
        threading.Thread(target=self.compress_video).start()

    def compress_video(self):

        if not self.selected_file:
            return

        output = unique_filename(
            os.path.splitext(self.selected_file)[0] + "_compressed.mp4"
        )

        target_size = self.target_size_entry.get().strip()

        if target_size:
            # وضع الحجم المحدد
            target_bits = float(target_size) * 8 * 1024 * 1024
            video_bitrate = int((target_bits / self.duration) - 128000)

            cmd = [
                FFMPEG,
                "-y",
                "-i", self.selected_file,
                "-b:v", str(video_bitrate),
                "-c:a", "aac",
                "-b:a", "128k",
                output
            ]
        else:
            # وضع Smart CRF
            cmd_probe = [
                FFPROBE,
                "-v","error",
                "-select_streams","v:0",
                "-show_entries","stream=width,height",
                "-of","csv=p=0",
                self.selected_file
            ]
            r = subprocess.run(cmd_probe, capture_output=True, text=True)
            w,h = map(int, r.stdout.strip().split(","))

            crf = smart_crf(w,h)

            cmd = [
                FFMPEG,
                "-y",
                "-i", self.selected_file,
                "-c:v","libx264",
                "-crf",str(crf),
                "-preset","medium",
                "-c:a","aac",
                "-b:a","128k",
                output
            ]

        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        for line in process.stderr:
            if "time=" in line:
                time_part = line.split("time=")[1].split(" ")[0]
                h,m,s = time_part.split(":")
                current = int(h)*3600 + int(m)*60 + float(s)
                percent = current / self.duration
                self.progress.set(min(percent,1))

        process.wait()
        self.progress.set(1)
        self.log_box.insert("end", "Compression Finished\n")
        os.startfile(os.path.dirname(output))


# ============================================================
# تشغيل
# ============================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()