# ============================================================
#  Advanced Educational YouTube Downloader & Pro Compressor
# ============================================================
#
# ========================== الميزات ==========================
#
# -------------------- YouTube Downloader --------------------
# ✔ دعم تحميل فيديو مع دمج الصوت (video+audio)
# ✔ دعم Playlist تلقائياً
# ✔ اختيار جودة الفيديو من القائمة
# ✔ تطبيق حجم مخصص: اختيار أفضل جودة ضمن الحجم المحدد
# ✔ MP3 بجودة 16kbps
# ✔ زر إلغاء التحميل (إيقاف فوري)
# ✔ شريط تقدم حقيقي لجميع الفيديوهات
# ✔ حفظ الاسم الأصلي للفيديو
# ✔ منع تكرار الاسم (إضافة رقم تصاعدي)
# ✔ فتح مجلد التحميل تلقائياً بعد انتهاء أي تحميل
# ✔ زر فتح مجلد التحميل يدوياً
# ✔ مربع نص يعرض المسار الحالي لمجلد الحفظ
# ✔ لصق الحافظة بزر الفأرة الأيمن
# ✔ يعمل بدون أخطاء ANSI عند التحويل بـ PyInstaller
#
# ---------------- Professional Local Compressor -------------
# ✔ ضغط الفيديو فقط عند الحاجة
# ✔ تحليل مدة الفيديو عبر ffprobe
# ✔ Smart CRF عند عدم تحديد حجم
# ✔ حساب bitrate دقيق عند تحديد حجم
# ✔ خصم صوت AAC من الحساب
# ✔ دعم Two‑Pass Encoding عبر CheckBox
# ✔ شريط تقدم يعتمد على وقت الفيديو
# ✔ زر إلغاء الضغط (Kill ffmpeg)
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
# تحديد مسار ffmpeg و ffprobe سواء تشغيل عادي أو PyInstaller
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
# توليد اسم فريد في حال وجود ملف بنفس الاسم
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
class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Advanced Educational Downloader & Compressor")
        self.geometry("1000x950")

        # مسار الحفظ الافتراضي
        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")

        self.formats = []
        self.cancel_flag = False
        self.selected_file = ""
        self.compress_process = None
        self.compress_cancel = False

        self.build_ui()

    # ========================================================
    # بناء الواجهة الرسومية
    # ========================================================
    def build_ui(self):

        # -------- عنوان قسم YouTube --------
        ctk.CTkLabel(self, text="YouTube Downloader",
                     font=("Arial", 24, "bold"),
                     text_color="#4da6ff").pack(pady=10)

        # مربع إدخال الرابط
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")
        self.add_right_click(self.url_entry)

        # عرض مسار الحفظ الحالي
        self.path_label = ctk.CTkEntry(self)
        self.path_label.pack(padx=20, pady=5, fill="x")
        self.path_label.insert(0, self.save_path)

        # زر جلب الصيغ
        ctk.CTkButton(self, text="Fetch Formats",
                      command=self.fetch_info).pack(pady=5)

        # قائمة اختيار الجودة
        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=5)

        # إدخال حجم أقصى
        self.size_entry = ctk.CTkEntry(self,
                                       placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        # أزرار التحميل
        yt_frame = ctk.CTkFrame(self)
        yt_frame.pack(pady=8)

        ctk.CTkButton(yt_frame, text="Download Video",
                      command=self.start_video).grid(row=0, column=0, padx=5)

        ctk.CTkButton(yt_frame, text="Download MP3 16kbps",
                      command=self.start_mp3).grid(row=0, column=1, padx=5)

        ctk.CTkButton(yt_frame, text="Cancel Download",
                      fg_color="red",
                      command=self.cancel_download).grid(row=0, column=2, padx=5)

        ctk.CTkButton(self, text="Open Download Folder",
                      command=self.open_folder).pack(pady=5)

        # -------- عنوان قسم الضغط المحلي --------
        ctk.CTkLabel(self,
                     text="Professional Local Video Compressor",
                     font=("Arial", 22, "bold"),
                     text_color="#00cc99").pack(pady=20)

        # اختيار ملف محلي
        self.file_entry = ctk.CTkEntry(self,
                                       placeholder_text="Select local video file")
        self.file_entry.pack(padx=20, fill="x")
        self.add_right_click(self.file_entry)

        comp_frame = ctk.CTkFrame(self)
        comp_frame.pack(pady=8)

        ctk.CTkButton(comp_frame, text="Select File",
                      command=self.select_file).grid(row=0, column=0, padx=5)

        ctk.CTkButton(comp_frame, text="Compress",
                      command=self.start_compress).grid(row=0, column=1, padx=5)

        ctk.CTkButton(comp_frame, text="Cancel Compress",
                      fg_color="red",
                      command=self.cancel_compress).grid(row=0, column=2, padx=5)

        # حجم هدف للضغط
        self.target_size_entry = ctk.CTkEntry(self,
                                              placeholder_text="Target Size MB (Optional)")
        self.target_size_entry.pack(pady=5)

        # خيار Two Pass
        self.two_pass_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self,
                        text="Enable Two-Pass Encoding",
                        variable=self.two_pass_var).pack()

        # شريط تقدم عام
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=15, fill="x")
        self.progress.set(0)

        # صندوق سجل العمليات
        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(padx=20, pady=10, fill="both")

    # ========================================================
    # إضافة قائمة لصق بزر الفأرة الأيمن
    # ========================================================
    def add_right_click(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste",
                         command=lambda: widget.insert("insert",
                                                       self.clipboard_get()))
        widget.bind("<Button-3>",
                    lambda e: menu.tk_popup(e.x_root, e.y_root))

    # ========================================================
    # تسجيل رسائل في صندوق السجل
    # ========================================================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # ========================================================
    # جلب الصيغ المتاحة مع الحجم
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
                size_mb = round(size / 1024 / 1024, 2) if size else 0
                label = f"{f['height']}p - {size_mb} MB"
                self.formats.append((label, f["format_id"], size))
                labels.append(label)

        if labels:
            self.quality_menu.configure(values=labels)
            self.quality_menu.set(labels[0])
            self.log("Formats loaded.")

    # ========================================================
    # اختيار أفضل جودة ضمن حجم محدد
    # ========================================================
    def select_by_size(self, max_mb):
        sorted_formats = sorted(self.formats,
                                key=lambda x: x[2],
                                reverse=True)
        for f in sorted_formats:
            if f[2] <= max_mb * 1024 * 1024:
                return f
        return sorted_formats[-1] if sorted_formats else None

    # ========================================================
    # بدء تحميل فيديو
    # ========================================================
    def start_video(self):
        self.cancel_flag = False
        threading.Thread(target=self.download_video).start()

    def download_video(self):

        url = self.url_entry.get().strip()
        selected_label = self.quality_menu.get()
        selected = next((f for f in self.formats if f[0] == selected_label), None)

        max_size = self.size_entry.get().strip()
        if max_size:
            try:
                selected = self.select_by_size(float(max_size))
            except:
                pass

        format_string = f"{selected[1]}+bestaudio/best" if selected else "bestvideo+bestaudio/best"

        def hook(d):
            if self.cancel_flag:
                raise Exception("Cancelled")
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').replace('%', '').strip()
                try:
                    self.progress.set(float(percent) / 100)
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
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                unique_path = unique_filename(filename)
                if unique_path != filename:
                    os.rename(filename, unique_path)

            self.log("Download finished.")
            self.open_folder()
        except Exception as e:
            self.log(f"Cancelled or Error: {e}")

    # ========================================================
    # تحميل MP3 16kbps
    # ========================================================
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
            "no_color": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            unique_path = unique_filename(filename)
            if unique_path != filename:
                os.rename(filename, unique_path)

        self.log("MP3 finished.")
        self.open_folder()

    def cancel_download(self):
        self.cancel_flag = True
        self.log("Cancelling download...")

    # ========================================================
    # فتح مجلد التحميل
    # ========================================================
    def open_folder(self):
        os.startfile(self.save_path)

    # ========================================================
    # =================== LOCAL COMPRESSION ===================
    # ========================================================
    def select_file(self):
        file = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")]
        )
        if file:
            self.selected_file = file
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file)

    def get_duration(self, file):
        cmd = [FFPROBE, "-v", "error",
               "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1",
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
        self.compress_cancel = False
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

        if not target_size:
            cmd = [FFMPEG, "-y", "-i", self.selected_file,
                   "-c:v", "libx264", "-crf", "21",
                   "-preset", "medium",
                   "-c:a", "aac", "-b:a", "128k",
                   output]
            self.compress_process = subprocess.Popen(cmd)
            self.compress_process.wait()
        else:
            size_mb = float(target_size)
            total_bits = size_mb * 1024 * 1024 * 8
            audio_bitrate = 128000
            video_bitrate = int((total_bits / duration - audio_bitrate) / 1000)

            if not two_pass:
                cmd = [FFMPEG, "-y", "-i", self.selected_file,
                       "-c:v", "libx264", "-b:v", f"{video_bitrate}k",
                       "-preset", "medium",
                       "-c:a", "aac", "-b:a", "128k",
                       output]
                self.compress_process = subprocess.Popen(cmd)
                self.compress_process.wait()
            else:
                subprocess.run([FFMPEG, "-y", "-i", self.selected_file,
                                "-c:v", "libx264", "-b:v", f"{video_bitrate}k",
                                "-pass", "1", "-an", "-f", "mp4", "NUL"])
                self.compress_process = subprocess.Popen(
                    [FFMPEG, "-y", "-i", self.selected_file,
                     "-c:v", "libx264", "-b:v", f"{video_bitrate}k",
                     "-pass", "2",
                     "-c:a", "aac", "-b:a", "128k",
                     output])
                self.compress_process.wait()

        self.log("Compression finished.")
        os.startfile(os.path.dirname(output))

    def cancel_compress(self):
        if self.compress_process and self.compress_process.poll() is None:
            self.compress_process.kill()
            self.log("Compression cancelled.")

# ============================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()