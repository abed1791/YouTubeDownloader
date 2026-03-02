# هذه نسخة تعليمية، كل سطر مشروح وتركز على المفاهيم الأساسية:

# Threads لتجنب تجميد الواجهة

# progress_hooks لمتابعة التحميل

# استخدام ffmpeg للضغط وتحويل الصوت

# قائمة منسدلة لاختيار الجودة

# حفظ الاسم الأصلي للفيديو

# استيراد المكتبات الأساسية
import os               # للتعامل مع الملفات والمجلدات
import threading        # لإنشاء خيوط (Threads) حتى لا تتجمد واجهة المستخدم أثناء التحميل
import customtkinter as ctk  # لإنشاء واجهة حديثة وجميلة
from tkinter import filedialog  # لفتح نافذة اختيار المجلد
import yt_dlp           # مكتبة تحميل الفيديوهات من يوتيوب
import subprocess       # لاستدعاء برامج خارجية مثل ffmpeg

# إعداد الثيم العام للواجهة
ctk.set_appearance_mode("dark")  # الوضع الليلي
ctk.set_default_color_theme("blue")  # اللون الأساسي

# القيمة الافتراضية لأقصى حجم فيديو بالميغابايت
DEFAULT_MAX_SIZE_MB = 49

# تعريف الكلاس الرئيسي للتطبيق
class App(ctk.CTk):
    def __init__(self):
        super().__init__()  # استدعاء الكونستركتور الأصلي
        self.title("YouTube Downloader Pro")  # عنوان النافذة
        self.geometry("650x500")  # حجم النافذة

        # متغيرات لتخزين الرابط، الجودات، ومسار الحفظ
        self.url = ""
        self.formats = []
        self.save_path = os.getcwd()  # افتراضياً المجلد الحالي

        # استدعاء الدالة التي تنشئ الواجهة
        self.create_ui()

    # دالة إنشاء الواجهة
    def create_ui(self):
        # مربع إدخال رابط الفيديو
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL")
        self.url_entry.pack(pady=10, padx=20, fill="x")

        # زر جلب معلومات الفيديو (مثل الجودات المتاحة)
        self.fetch_btn = ctk.CTkButton(self, text="Fetch Info", command=self.fetch_info)
        self.fetch_btn.pack(pady=5)

        # قائمة منسدلة لاختيار الجودة
        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=10)

        # مربع إدخال الحجم الأقصى (اختياري)
        self.size_entry = ctk.CTkEntry(self, placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        # شريط تقدم التحميل
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(pady=10, fill="x", padx=20)
        self.progress.set(0)

        # صندوق لعرض سجل التحميل والرسائل
        self.log = ctk.CTkTextbox(self, height=120)
        self.log.pack(pady=10, padx=20, fill="both")

        # إطار يحتوي أزرار التحميل
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        # زر تحميل الفيديو
        self.video_btn = ctk.CTkButton(btn_frame, text="Download Video", command=self.download_video)
        self.video_btn.grid(row=0, column=0, padx=10)

        # زر تحميل الصوت فقط MP3 32kbps
        self.mp3_btn = ctk.CTkButton(btn_frame, text="Download MP3 32kbps", command=self.download_mp3)
        self.mp3_btn.grid(row=0, column=1, padx=10)

        # زر اختيار مجلد الحفظ
        self.path_btn = ctk.CTkButton(self, text="Select Save Folder", command=self.select_folder)
        self.path_btn.pack(pady=5)

    # دالة لكتابة الرسائل في صندوق السجل
    def log_write(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")  # تمرير تلقائي للأسفل

    # دالة اختيار مجلد الحفظ
    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path = path
            self.log_write(f"Save Path: {path}")

    # دالة جلب معلومات الفيديو (عنوان، جودات، أحجام)
    def fetch_info(self):
        self.url = self.url_entry.get().strip()
        if not self.url:
            return

        self.log_write("Fetching info...")
        ydl_opts = {"quiet": True}  # عدم عرض الكثير من الرسائل
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)  # فقط المعلومات

        self.title_name = info.get("title", "video")
        formats = info.get("formats", [])

        self.formats = []
        qualities = []

        # استخراج جميع الجودات المتاحة
        for f in formats:
            if f.get("height") and f.get("ext") == "mp4":
                size = f.get("filesize") or 0
                label = f"{f['height']}p - {round(size/1024/1024,2)} MB"
                qualities.append(label)
                self.formats.append((label, f["format_id"], size))

        self.quality_menu.configure(values=qualities)
        self.quality_menu.set(qualities[0])
        self.log_write("Formats Loaded")

    # دالة تحديث شريط التقدم أثناء التحميل
    def hook(self, d):
        if d['status'] == 'downloading':
            percent = float(d['_percent_str'].replace('%',''))
            self.progress.set(percent/100)
        if d['status'] == 'finished':
            self.progress.set(1)

    # دالة لاختيار أفضل جودة ضمن الحجم الأقصى
    def select_best_format(self, max_size_mb):
        sorted_formats = sorted(self.formats, key=lambda x: x[2], reverse=True)
        for f in sorted_formats:
            if f[2] <= max_size_mb * 1024 * 1024:
                return f
        return sorted_formats[-1]

    # زر تحميل الفيديو
    def download_video(self):
        threading.Thread(target=self._download_video).start()  # إنشاء Thread لتجنب تجميد الواجهة

    def _download_video(self):
        try:
            max_size = float(self.size_entry.get()) if self.size_entry.get() else None
        except:
            max_size = None

        selected_label = self.quality_menu.get()
        selected = next((f for f in self.formats if f[0] == selected_label), None)

        if max_size:
            selected = self.select_best_format(max_size)

        filename = os.path.join(self.save_path, self.title_name + ".mp4")

        ydl_opts = {
            "format": selected[1],
            "outtmpl": filename,
            "progress_hooks": [self.hook],
            "ffmpeg_location": "./ffmpeg.exe",
            "nopart": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])

        # ضغط الفيديو إذا كان أكبر من الحجم المخصص
        if max_size:
            size_mb = os.path.getsize(filename) / (1024*1024)
            if size_mb > max_size:
                compressed = filename.replace(".mp4","_compressed.mp4")
                subprocess.run([
                    "./ffmpeg.exe","-i",filename,
                    "-vcodec","libx264","-crf","28",
                    compressed
                ])
                os.remove(filename)
                os.rename(compressed, filename)

        self.log_write("Download Complete")

    # زر تحميل MP3 فقط
    def download_mp3(self):
        threading.Thread(target=self._download_mp3).start()

    def _download_mp3(self):
        filename = os.path.join(self.save_path, self.title_name + ".%(ext)s")

        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": filename,
            "progress_hooks": [self.hook],
            "ffmpeg_location": "./ffmpeg.exe",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "32"
            }],
            "nopart": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])

        self.log_write("MP3 Download Complete")


# تشغيل التطبيق
if __name__ == "__main__":
    app = App()
    app.mainloop()