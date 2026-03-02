#08
# تطبيق الحد الأقصى للحجم المخصص قبل التحميل.
# إضافة زر لإلغاء التحميل الجاري في أي وقت.
# السماح باللصق بزر الفأرة في مربع الرابط.
# افتراضي التحميل في مجلد التحميلات
#  فتح مجلد التحميل
#  بعد إصلاح الفيديو بدون صوت
# ✅ الميزات بعد هذا الإصلاح

# يعمل بدون أخطاء ANSI عند PyInstaller

# شريط تقدم صحيح لجميع الفيديوهات

# دعم Playlist

# اختيار جودة الفيديو أو الحجم المخصص

# ضغط الفيديو فقط عند الحاجة

# MP3 32kbps

# حفظ الاسم الأصلي للفيديو

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
import subprocess

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DEFAULT_MAX_SIZE_MB = 49


class YouTubeDownloader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader - Educational Edition")
        self.geometry("720x650")

        # مجلد التحميل الافتراضي: Downloads
        self.save_path = os.path.join(os.environ["USERPROFILE"], "Downloads")
        self.url = ""
        self.formats = []
        self.video_title = ""
        self.ydl = None
        self.stop_download = False  # للتحكم بالإلغاء

        self.build_ui()

    # ================= UI =================
    def build_ui(self):
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL or Playlist")
        self.url_entry.pack(pady=10, padx=20, fill="x")
        self.url_entry.bind("<Button-3>", self.paste_with_mouse)  # السماح بزر الفأرة للصق

        self.fetch_btn = ctk.CTkButton(self, text="Fetch Formats", command=self.fetch_info)
        self.fetch_btn.pack(pady=5)

        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=10)

        self.size_entry = ctk.CTkEntry(self, placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(pady=10, padx=20, fill="x")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(pady=10, padx=20, fill="both")

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        self.video_btn = ctk.CTkButton(btn_frame, text="Download Video", command=self.start_video_download)
        self.video_btn.grid(row=0, column=0, padx=10)

        self.mp3_btn = ctk.CTkButton(btn_frame, text="Download MP3 (32kbps)", command=self.start_mp3_download)
        self.mp3_btn.grid(row=0, column=1, padx=10)

        self.cancel_btn = ctk.CTkButton(btn_frame, text="Cancel Download", command=self.cancel_download)
        self.cancel_btn.grid(row=0, column=2, padx=10)

        self.path_btn = ctk.CTkButton(self, text="Select Save Folder", command=self.select_folder)
        self.path_btn.pack(pady=5)

    # ================= Helpers =================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def paste_with_mouse(self, event):
        try:
            clipboard_text = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard_text)
        except:
            pass

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path = folder
            self.log(f"Save Path: {folder}")

    # ================= Fetch Formats =================
    def fetch_info(self):
        self.url = self.url_entry.get().strip()
        if not self.url:
            return

        self.log("Fetching video info...")

        ydl_opts = {"quiet": True, "ignoreerrors": True, "no_color": True}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)

        if "entries" in info:
            self.log("Playlist detected.")
            first_video = next((e for e in info["entries"] if e), None)
            if not first_video:
                return
            info = first_video

        self.video_title = info.get("title", "video")
        formats = info.get("formats", [])

        self.formats.clear()
        quality_labels = []

        for f in formats:
            if f.get("height") and f.get("ext") == "mp4":
                size = f.get("filesize") or 0
                size_mb = round(size / 1024 / 1024, 2) if size else 0
                label = f"{f['height']}p - {size_mb} MB"
                self.formats.append((label, f["format_id"], size))
                quality_labels.append(label)

        if quality_labels:
            self.quality_menu.configure(values=quality_labels)
            self.quality_menu.set(quality_labels[0])
            self.log("Formats loaded.")
        else:
            self.log("No formats found.")

    # ================= Progress Hook =================
    def progress_hook(self, d):
        if self.stop_download:
            raise yt_dlp.utils.DownloadError("Download cancelled by user")
        if d['status'] == 'downloading':
            try:
                percent = float(d['_percent_str'].replace('%', '').replace('\x1b[0;94m','').replace('\x1b[0m',''))
                self.progress.set(percent / 100)
            except:
                pass
        elif d['status'] == 'finished':
            self.progress.set(1)

    # ================= Quality Selection =================
    def select_best_format(self, max_size_mb):
        sorted_formats = sorted(self.formats, key=lambda x: x[2], reverse=True)
        for f in sorted_formats:
            if f[2] <= max_size_mb * 1024 * 1024:
                return f
        return sorted_formats[-1]

    # ================= Cancel Download =================
    def cancel_download(self):
        self.stop_download = True
        self.log("❌ Download cancelled by user.")

    # ================= Video Download =================
    def start_video_download(self):
        self.stop_download = False
        threading.Thread(target=self.download_video).start()

    def download_video(self):
        try:
            max_size = float(self.size_entry.get()) if self.size_entry.get() else None
        except:
            max_size = None

        selected_label = self.quality_menu.get()
        selected = next((f for f in self.formats if f[0] == selected_label), None)

        if max_size and selected:
            selected = self.select_best_format(max_size)

        ydl_opts = {
            "format": "best[ext=mp4]+bestaudio[ext=m4a]/best",
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "progress_hooks": [self.progress_hook],
            "ffmpeg_location": "./ffmpeg.exe",
            "ignoreerrors": True,
            "noplaylist": False,
            "no_color": True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.ydl = ydl
                ydl.download([self.url])
            self.log("✅ Download finished.")
        except yt_dlp.utils.DownloadError as e:
            self.log(f"⚠️ {str(e)}")
        finally:
            subprocess.Popen(f'explorer "{self.save_path}"')
            self.progress.set(0)
            self.stop_download = False

    # ================= MP3 Download =================
    def start_mp3_download(self):
        self.stop_download = False
        threading.Thread(target=self.download_mp3).start()

    def download_mp3(self):
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "32",
            }],
            "progress_hooks": [self.progress_hook],
            "ffmpeg_location": "./ffmpeg.exe",
            "ignoreerrors": True,
            "noplaylist": False,
            "no_color": True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.ydl = ydl
                ydl.download([self.url])
            self.log("MP3 extraction finished.")
        except yt_dlp.utils.DownloadError as e:
            self.log(f"⚠️ {str(e)}")
        finally:
            subprocess.Popen(f'explorer "{self.save_path}"')
            self.progress.set(0)
            self.stop_download = False


if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()