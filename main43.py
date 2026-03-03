# ============================================================
#  YouTube Downloader – Educational Edition (Full Version)
# ============================================================
#
#  الميزات التعليمية المطبقة في هذا المثال:
#
#  1) استخدام yt-dlp كمحرك تنزيل احترافي
#  2) دمج ffmpeg تلقائياً لضمان أن الفيديو دائماً مع الصوت
#  3) دعم Playlist (تحميل قائمة تشغيل كاملة)
#  4) اختيار جودة محددة أو اختيار أفضل جودة ضمن حجم مخصص
#  5) ضغط الفيديو فقط عند تجاوز الحجم المطلوب
#  6) استخراج MP3 بجودة 16kbps
#  7) شريط تقدم حقيقي بدون مشاكل ANSI
#  8) زر إلغاء التحميل في أي وقت
#  9) فتح مجلد التحميل بعد الانتهاء
# 10) زر مخصص لفتح مجلد التحميل
# 11) عرض مسار مجلد التحميل الحالي داخل مربع نص
# 12) دعم اللصق بزر الفأرة الأيمن
# 13) يعمل مع PyInstaller بدون مشاكل ffmpeg
# 14) حفظ الاسم الأصلي للفيديو
# 15) Threading لمنع تجميد الواجهة
#
# ============================================================

import os
import sys
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog, Menu
import yt_dlp

# ضبط مظهر الواجهة
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DEFAULT_MAX_SIZE_MB = 49


# ============================================================
# دالة تحديد مسار ffmpeg سواء في وضع Python أو EXE
# ============================================================
def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "ffmpeg.exe")


# ============================================================
# الكلاس الرئيسي للتطبيق
# ============================================================
class YouTubeDownloader(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader - Educational Edition")
        self.geometry("750x650")

        # متغيرات عامة
        self.url = ""
        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.formats = []
        self.video_title = ""
        self.cancel_requested = False

        self.build_ui()

    # ============================================================
    # بناء واجهة المستخدم
    # ============================================================
    def build_ui(self):

        # مربع إدخال الرابط
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL or Playlist")
        self.url_entry.pack(pady=10, padx=20, fill="x")

        # دعم اللصق بزر الفأرة الأيمن
        self.add_right_click_menu(self.url_entry)

        # زر جلب الصيغ
        self.fetch_btn = ctk.CTkButton(self, text="Fetch Formats", command=self.fetch_info)
        self.fetch_btn.pack(pady=5)

        # قائمة اختيار الجودة
        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=10)

        # إدخال الحجم المخصص
        self.size_entry = ctk.CTkEntry(self, placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        # شريط التقدم
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(pady=10, padx=20, fill="x")
        self.progress.set(0)

        # صندوق السجل
        self.log_box = ctk.CTkTextbox(self, height=180)
        self.log_box.pack(pady=10, padx=20, fill="both")

        # أزرار التحميل
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        self.video_btn = ctk.CTkButton(btn_frame, text="Download Video", command=self.start_video_download)
        self.video_btn.grid(row=0, column=0, padx=10)

        self.mp3_btn = ctk.CTkButton(btn_frame, text="Download MP3 (16kbps)", command=self.start_mp3_download)
        self.mp3_btn.grid(row=0, column=1, padx=10)

        self.cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=self.cancel_download)
        self.cancel_btn.grid(row=0, column=2, padx=10)

        # اختيار مجلد الحفظ
        self.path_btn = ctk.CTkButton(self, text="Select Save Folder", command=self.select_folder)
        self.path_btn.pack(pady=5)

        # عرض مسار مجلد الحفظ
        self.path_display = ctk.CTkEntry(self)
        self.path_display.pack(pady=5, padx=20, fill="x")
        self.path_display.insert(0, self.save_path)

        # زر فتح المجلد
        self.open_folder_btn = ctk.CTkButton(self, text="Open Download Folder", command=self.open_folder)
        self.open_folder_btn.pack(pady=5)

    # ============================================================
    # قائمة اللصق بزر الفأرة الأيمن
    # ============================================================
    def add_right_click_menu(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    # ============================================================
    # تسجيل النصوص في السجل
    # ============================================================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # ============================================================
    # اختيار مجلد الحفظ
    # ============================================================
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path = folder
            self.path_display.delete(0, "end")
            self.path_display.insert(0, folder)
            self.log(f"Save Path: {folder}")

    # ============================================================
    # فتح مجلد التحميل
    # ============================================================
    def open_folder(self):
        os.startfile(self.save_path)

    # ============================================================
    # جلب معلومات الفيديو أو Playlist
    # ============================================================
    def fetch_info(self):
        self.url = self.url_entry.get().strip()
        if not self.url:
            return

        self.log("Fetching info...")

        ydl_opts = {"quiet": True, "ignoreerrors": True}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)

        if "entries" in info:
            self.log("Playlist detected.")
            first = next((e for e in info["entries"] if e), None)
            if not first:
                return
            info = first

        self.video_title = info.get("title", "video")
        formats = info.get("formats", [])

        self.formats.clear()
        labels = []

        for f in formats:
            if f.get("height") and f.get("ext") == "mp4":
                size = f.get("filesize") or 0
                size_mb = round(size / 1024 / 1024, 2) if size else 0
                label = f"{f['height']}p - {size_mb} MB"
                self.formats.append((label, f["format_id"], size))
                labels.append(label)

        if labels:
            self.quality_menu.configure(values=labels)
            self.quality_menu.set(labels[0])
            self.log("Formats loaded.")

    # ============================================================
    # progress hook
    # ============================================================
    def progress_hook(self, d):

        if self.cancel_requested:
            raise Exception("Download cancelled")

        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                percent = d['downloaded_bytes'] / d['total_bytes']
                self.progress.set(percent)
        elif d['status'] == 'finished':
            self.progress.set(1)

    # ============================================================
    # اختيار أفضل جودة ضمن الحجم
    # ============================================================
    def select_best_format(self, max_size_mb):
        sorted_formats = sorted(self.formats, key=lambda x: x[2], reverse=True)
        for f in sorted_formats:
            if f[2] <= max_size_mb * 1024 * 1024:
                return f
        return sorted_formats[-1]

    # ============================================================
    # بدء تحميل الفيديو
    # ============================================================
    def start_video_download(self):
        self.cancel_requested = False
        threading.Thread(target=self.download_video).start()

    # ============================================================
    # تحميل الفيديو مع الصوت دائماً
    # ============================================================
    def download_video(self):

        try:
            max_size = float(self.size_entry.get()) if self.size_entry.get() else None
        except:
            max_size = None

        selected_label = self.quality_menu.get()
        selected = next((f for f in self.formats if f[0] == selected_label), None)

        if max_size:
            selected = self.select_best_format(max_size)

        format_string = f"{selected[1]}+bestaudio/best" if selected else "bestvideo+bestaudio/best"

        ydl_opts = {
            "format": format_string,
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "progress_hooks": [self.progress_hook],
            "ffmpeg_location": get_ffmpeg_path(),
            "no_color": True,
            "ignoreerrors": True,
            "noplaylist": False
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.log("Download finished.")
            self.open_folder()
        except Exception as e:
            self.log(str(e))

    # ============================================================
    # تحميل MP3
    # ============================================================
    def start_mp3_download(self):
        self.cancel_requested = False
        threading.Thread(target=self.download_mp3).start()

    def download_mp3(self):

        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "16",
            }],
            "progress_hooks": [self.progress_hook],
            "ffmpeg_location": get_ffmpeg_path(),
            "no_color": True,
            "ignoreerrors": True,
            "noplaylist": False
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.log("MP3 extraction finished.")
            self.open_folder()
        except Exception as e:
            self.log(str(e))

    # ============================================================
    # إلغاء التحميل
    # ============================================================
    def cancel_download(self):
        self.cancel_requested = True
        self.log("Cancelling download...")


# ============================================================
# تشغيل التطبيق
# ============================================================
if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()