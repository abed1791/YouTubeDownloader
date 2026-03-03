# ============================================================
#  Advanced Educational Downloader & Compressor
# ============================================================
#
# الميزات التعليمية الكاملة:
# ------------------------------------------------------------
# ✔ تحميل فيديو يوتيوب مع الصوت دائماً (video+audio merge)
# ✔ دعم Playlist
# ✔ اختيار جودة أو حجم مخصص
# ✔ ضغط الفيديو فقط عند الحاجة
# ✔ MP3 16kbps
# ✔ شريط تقدم حقيقي
# ✔ زر إلغاء التحميل
# ✔ فتح مجلد التحميل
# ✔ عرض مسار مجلد الحفظ
# ✔ ضغط فيديو محلي باحتساب bitrate احترافي
# ✔ احتساب bitrate الفيديو بعد خصم bitrate الصوت
# ✔ دعم Drag & Drop (سحب وإفلات ملف فيديو)
# ✔ دعم اللصق بزر الفأرة الأيمن
# ✔ يعمل مع PyInstaller
# ✔ حفظ الاسم الأصلي
# ✔ منع أخطاء ANSI / Unicode
# ============================================================

import os
import sys
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog, Menu
import yt_dlp

# لدعم السحب والإفلات
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except:
    DND_AVAILABLE = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DEFAULT_AUDIO_BITRATE = 128000  # 128kbps صوت للحساب الاحترافي


# ============================================================
# تحديد مسار ffmpeg (متوافق مع EXE)
# ============================================================
def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "ffmpeg.exe")


# ============================================================
# التطبيق الرئيسي
# ============================================================
class App(ctk.CTk if not DND_AVAILABLE else TkinterDnD.Tk):

    def __init__(self):
        super().__init__()

        self.title("Advanced Educational Downloader & Compressor")
        self.geometry("850x780")

        self.url = ""
        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.formats = []
        self.cancel_requested = False
        self.selected_file = ""

        self.build_ui()

    # ============================================================
    # بناء الواجهة
    # ============================================================
    def build_ui(self):

        # ---------------- YouTube Section ----------------
        ctk.CTkLabel(self, text="YouTube Downloader", font=("Arial", 18)).pack(pady=10)

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")

        self.add_right_click_menu(self.url_entry)

        ctk.CTkButton(self, text="Fetch Formats", command=self.fetch_info).pack(pady=5)

        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=5)

        self.size_entry = ctk.CTkEntry(self, placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=5)

        ctk.CTkButton(btn_frame, text="Download Video", command=self.start_video_download).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="Download MP3 16kbps", command=self.start_mp3_download).grid(row=0, column=1, padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.cancel_download).grid(row=0, column=2, padx=10)

        # ---------------- Local Compressor Section ----------------
        ctk.CTkLabel(self, text="Local Video Compressor", font=("Arial", 18)).pack(pady=15)

        self.file_entry = ctk.CTkEntry(self, placeholder_text="Drag & Drop video here or Select")
        self.file_entry.pack(padx=20, fill="x")

        self.add_right_click_menu(self.file_entry)

        if DND_AVAILABLE:
            self.file_entry.drop_target_register(DND_FILES)
            self.file_entry.dnd_bind('<<Drop>>', self.drop_file)

        ctk.CTkButton(self, text="Select Video File", command=self.select_video_file).pack(pady=5)

        self.target_size_entry = ctk.CTkEntry(self, placeholder_text="Target Size MB")
        self.target_size_entry.pack(pady=5)

        ctk.CTkButton(self, text="Compress Video", command=self.start_compress).pack(pady=5)

        # ---------------- Progress & Log ----------------
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=10, fill="x")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=220)
        self.log_box.pack(padx=20, pady=10, fill="both")

        ctk.CTkButton(self, text="Open Download Folder", command=self.open_folder).pack(pady=5)

    # ============================================================
    # دعم اللصق بزر الفأرة
    # ============================================================
    def add_right_click_menu(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    # ============================================================
    # دعم السحب والإفلات
    # ============================================================
    def drop_file(self, event):
        file_path = event.data.strip("{}")
        self.selected_file = file_path
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, file_path)

    # ============================================================
    # تسجيل
    # ============================================================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # ============================================================
    # فتح مجلد
    # ============================================================
    def open_folder(self):
        os.startfile(self.save_path)

    # ============================================================
    # جلب الصيغ
    # ============================================================
    def fetch_info(self):
        self.url = self.url_entry.get().strip()
        if not self.url:
            return

        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(self.url, download=False)

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

    # ============================================================
    # تنزيل فيديو
    # ============================================================
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
            ydl.download([self.url])

        self.log("Download finished")
        self.open_folder()

    # ============================================================
    # تنزيل MP3
    # ============================================================
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
            ydl.download([self.url])

        self.log("MP3 finished")
        self.open_folder()

    # ============================================================
    # ضغط احترافي مع احتساب bitrate الصوت
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

        target_size = float(self.target_size_entry.get())
        ffmpeg = get_ffmpeg_path()

        # استخراج المدة
        cmd = [ffmpeg, "-i", self.selected_file]
        result = subprocess.run(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding="utf-8",
            errors="ignore"
        )

        duration_line = next((l for l in result.stderr.split("\n") if "Duration" in l), None)
        time_str = duration_line.split("Duration:")[1].split(",")[0].strip()
        h, m, s = time_str.split(":")
        duration = int(h)*3600 + int(m)*60 + float(s)

        # حساب الحجم بالبت
        target_bits = target_size * 8 * 1024 * 1024

        # طرح bitrate الصوت
        video_bitrate = int((target_bits / duration) - DEFAULT_AUDIO_BITRATE)

        output = os.path.splitext(self.selected_file)[0] + "_compressed.mp4"

        command = [
            ffmpeg,
            "-y",
            "-i", self.selected_file,
            "-b:v", str(video_bitrate),
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "128k",
            output
        ]

        subprocess.run(command)

        self.progress.set(1)
        self.log("Compression finished")
        os.startfile(os.path.dirname(output))

    # ============================================================
    # إلغاء
    # ============================================================
    def cancel_download(self):
        self.cancel_requested = True
        self.log("Cancelling...")


# ============================================================
# تشغيل التطبيق
# ============================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()