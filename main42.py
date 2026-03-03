# ==============================================================
# YouTube Downloader - Educational Edition (Final Stable Build)
# ==============================================================

# الميزات:
# ✔ الفيديو دائمًا مع الصوت (دمج format_id + bestaudio)
# ✔ اختيار جودة أو تحديد حجم مخصص
# ✔ اختيار أفضل جودة ضمن الحجم المحدد
# ✔ ضغط الفيديو فقط إذا تجاوز الحجم بعد التحميل
# ✔ دعم Playlist
# ✔ MP3 بجودة 16kbps
# ✔ زر إلغاء التحميل فورًا
# ✔ شريط تقدم دقيق بدون ANSI
# ✔ فتح مجلد التحميل بعد الانتهاء
# ✔ زر مستقل لفتح مجلد التحميل
# ✔ عرض المسار الحالي لمجلد التحميل
# ✔ لصق بزر الفأرة
# ✔ حفظ الاسم الأصلي للفيديو
# ✔ يعمل مع PyInstaller بدون مشاكل ANSI
# ✔ Threading لمنع تجميد الواجهة
# ==============================================================

import os
import threading
import customtkinter as ctk
from tkinter import filedialog
import yt_dlp
import subprocess

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DEFAULT_MAX_SIZE_MB = 49


class YouTubeDownloader(ctk.CTk):

    # ==========================================================
    # تهيئة التطبيق
    # ==========================================================
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader - Educational Edition")
        self.geometry("760x720")

        # مجلد التحميل الافتراضي
        self.save_path = os.path.join(os.environ["USERPROFILE"], "Downloads")

        self.url = ""
        self.formats = []
        self.stop_download = False

        self.build_ui()

    # ==========================================================
    # بناء واجهة المستخدم
    # ==========================================================
    def build_ui(self):

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL or Playlist")
        self.url_entry.pack(pady=10, padx=20, fill="x")
        self.url_entry.bind("<Button-3>", self.paste_url)

        self.fetch_btn = ctk.CTkButton(self, text="Fetch Formats", command=self.fetch_info)
        self.fetch_btn.pack(pady=5)

        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=10)

        self.size_entry = ctk.CTkEntry(self, placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        # عرض مسار الحفظ الحالي
        self.path_display = ctk.CTkEntry(self)
        self.path_display.pack(pady=5, padx=20, fill="x")
        self.path_display.insert(0, self.save_path)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(pady=10, padx=20, fill="x")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=220)
        self.log_box.pack(pady=10, padx=20, fill="both")

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        self.video_btn = ctk.CTkButton(btn_frame, text="Download Video", command=self.start_video_download)
        self.video_btn.grid(row=0, column=0, padx=5)

        self.mp3_btn = ctk.CTkButton(btn_frame, text="Download MP3 (16kbps)", command=self.start_mp3_download)
        self.mp3_btn.grid(row=0, column=1, padx=5)

        self.cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=self.cancel_download)
        self.cancel_btn.grid(row=0, column=2, padx=5)

        self.open_btn = ctk.CTkButton(btn_frame, text="Open Folder", command=self.open_folder)
        self.open_btn.grid(row=0, column=3, padx=5)

        self.select_btn = ctk.CTkButton(self, text="Select Save Folder", command=self.select_folder)
        self.select_btn.pack(pady=5)

    # ==========================================================
    # أدوات مساعدة
    # ==========================================================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def paste_url(self, event):
        try:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, self.clipboard_get())
        except:
            pass

    def open_folder(self):
        subprocess.Popen(f'explorer "{self.save_path}"')

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path = folder
            self.path_display.delete(0, "end")
            self.path_display.insert(0, folder)

    # ==========================================================
    # جلب معلومات الفيديو / Playlist
    # ==========================================================
    def fetch_info(self):
        self.url = self.url_entry.get().strip()
        if not self.url:
            return

        self.log("Fetching info...")

        with yt_dlp.YoutubeDL({"quiet": True, "no_color": True}) as ydl:
            info = ydl.extract_info(self.url, download=False)

        # دعم Playlist
        if "entries" in info:
            self.log("Playlist detected.")
            info = next((e for e in info["entries"] if e), None)

        self.formats.clear()
        labels = []

        for f in info.get("formats", []):
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

    # ==========================================================
    # شريط التقدم + الإلغاء
    # ==========================================================
    def progress_hook(self, d):

        if self.stop_download:
            raise yt_dlp.utils.DownloadError("Cancelled by user")

        if d['status'] == 'downloading':
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)

            if total:
                self.progress.set(downloaded / total)

        elif d['status'] == 'finished':
            self.progress.set(1)

    def cancel_download(self):
        self.stop_download = True
        self.log("Download cancelled.")

    # ==========================================================
    # اختيار أفضل جودة ضمن الحجم المحدد
    # ==========================================================
    def select_best_format(self, max_size_mb):
        sorted_formats = sorted(self.formats, key=lambda x: x[2], reverse=True)
        for f in sorted_formats:
            if f[2] <= max_size_mb * 1024 * 1024:
                return f
        return sorted_formats[-1]

    # ==========================================================
    # تنزيل الفيديو (دائمًا مع الصوت)
    # ==========================================================
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

        if max_size:
            selected = self.select_best_format(max_size)

        # الدمج الصحيح لضمان الصوت دائمًا
        format_string = f"{selected[1]}+bestaudio/best" if selected else "bestvideo+bestaudio/best"

        ydl_opts = {
            "format": format_string,
            "outtmpl": os.path.join(self.save_path, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "progress_hooks": [self.progress_hook],
            "ffmpeg_location": "./ffmpeg.exe",
            "no_color": True,
            "noplaylist": False
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            # ضغط فقط إذا تجاوز الحجم
            if max_size:
                latest_file = max(
                    [os.path.join(self.save_path, f) for f in os.listdir(self.save_path)],
                    key=os.path.getctime
                )

                size_mb = os.path.getsize(latest_file) / (1024 * 1024)

                if size_mb > max_size:
                    compressed = latest_file.replace(".mp4", "_compressed.mp4")

                    subprocess.run([
                        "ffmpeg", "-i", latest_file,
                        "-vcodec", "libx264",
                        "-crf", "28",
                        compressed
                    ])

                    os.remove(latest_file)

            self.log("Download finished.")
            self.open_folder()

        except Exception as e:
            self.log(str(e))

        self.progress.set(0)

    # ==========================================================
    # تنزيل MP3 16kbps
    # ==========================================================
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
                "preferredquality": "16",
            }],
            "progress_hooks": [self.progress_hook],
            "ffmpeg_location": "./ffmpeg.exe",
            "no_color": True,
            "noplaylist": False
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            self.log("MP3 finished.")
            self.open_folder()

        except Exception as e:
            self.log(str(e))

        self.progress.set(0)


# ==========================================================
# تشغيل التطبيق
# ==========================================================
if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()