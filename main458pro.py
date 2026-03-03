# ============================================================
#  Advanced Educational YouTube Downloader & Video Compressor
# ============================================================
#
# ======================= الميزات ============================
#
# قسم YouTube Downloader:
# ✔ تحميل فيديو مع الصوت دائماً (دمج video+audio)
# ✔ دعم Playlist
# ✔ اختيار جودة مع عرض الحجم
# ✔ اختيار حجم مخصص واختيار أفضل جودة ضمنه
# ✔ MP3 16kbps
# ✔ زر إلغاء التحميل الفوري
# ✔ شريط تقدم دقيق
# ✔ حفظ الاسم الأصلي
# ✔ منع تكرار الاسم (إضافة رقم تصاعدي)
# ✔ فتح مجلد التحميل تلقائياً
# ✔ زر فتح مجلد التحميل
# ✔ عرض مسار مجلد الحفظ
# ✔ دعم اللصق بزر الفأرة الأيمن
# ✔ بدون أخطاء Unicode / ANSI
#
# قسم Professional Local Video Compressor:
# ✔ تحليل مدة الفيديو عبر ffprobe
# ✔ حساب bitrate دقيق عند تحديد حجم نهائي
# ✔ Smart CRF عند عدم تحديد حجم
# ✔ حساب bitrate الفيديو بعد خصم صوت AAC
# ✔ شريط تقدم حقيقي يعتمد على مدة الفيديو
# ✔ دعم الإلغاء
# ✔ قراءة تقدم ffmpeg من stderr
# ✔ اسم ملف ناتج فريد
# ✔ يعمل مع أي فيديو يدعمه ffmpeg
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

# ============================================================
# إعداد مظهر الواجهة
# ============================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================
# تحديد مسار ffmpeg و ffprobe
# ============================================================
def get_ffmpeg():
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "ffmpeg.exe")

FFMPEG = get_ffmpeg()

# ============================================================
# منع تكرار الاسم (توليد اسم فريد تلقائياً)
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

        self.title("Eng. Abdul Baset Alsulaiman Educational YouTube Downloader & Compressor V458pro")
        self.geometry("950x820")

        # مجلد الحفظ الافتراضي
        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # متغيرات قسم YouTube
        self.formats = []
        self.cancel_flag = False

        # متغيرات قسم الضغط المحلي
        self.selected_file = ""
        self.compress_cancel = False

        self.build_ui()

    # ========================================================
    # بناء الواجهة الرسومية
    # ========================================================
    def build_ui(self):

        # ===================== YouTube Downloader ====================
        ctk.CTkLabel(self,
                     text="YouTube Downloader",
                     font=("Arial", 24, "bold"),
                     text_color="#4da6ff").pack(pady=15)

        # إدخال رابط الفيديو
        self.url_entry = ctk.CTkEntry(self,
                                      placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")
        self.add_right_click(self.url_entry)

        # زر جلب الصيغ
        ctk.CTkButton(self,
                      text="Fetch Formats",
                      command=self.fetch_info).pack(pady=8)

        # قائمة اختيار الجودة
        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=5)

        # إدخال حجم أقصى (اختياري)
        self.size_entry = ctk.CTkEntry(self, placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        # أزرار العمليات
        yt_buttons = ctk.CTkFrame(self)
        yt_buttons.pack(pady=10)

        ctk.CTkButton(yt_buttons, text="Download Video",
                      width=160, command=self.start_video).grid(row=0, column=0, padx=5)

        ctk.CTkButton(yt_buttons, text="Download MP3 16kbps",
                      width=160, command=self.start_mp3).grid(row=0, column=1, padx=5)

        ctk.CTkButton(yt_buttons, text="Cancel",
                      width=120, fg_color="red", command=self.cancel_download).grid(row=0, column=2, padx=5)

        # عرض مسار الحفظ
        self.path_label = ctk.CTkLabel(self, text=f"Save Path: {self.save_path}",
                                       text_color="#cccccc")
        self.path_label.pack(pady=5)

        # زر فتح المجلد
        ctk.CTkButton(self, text="Open Download Folder", command=self.open_folder).pack(pady=5)

        # ===================== Professional Local Video Compressor ====================
        ctk.CTkLabel(self,
                     text="Professional Local Video Compressor",
                     font=("Arial", 22, "bold"),
                     text_color="#00cc99").pack(pady=20)

        self.file_entry = ctk.CTkEntry(self, placeholder_text="Select local video file")
        self.file_entry.pack(padx=20, fill="x")

        comp_buttons = ctk.CTkFrame(self)
        comp_buttons.pack(pady=8)

        ctk.CTkButton(comp_buttons, text="Select File", width=160,
                      command=self.select_file).grid(row=0, column=0, padx=5)

        ctk.CTkButton(comp_buttons, text="Compress", width=160,
                      command=self.start_compress).grid(row=0, column=1, padx=5)

        self.target_size_entry = ctk.CTkEntry(self, placeholder_text="Target Size MB (Optional)")
        self.target_size_entry.pack(pady=5)

        # ===================== Progress & Log ======================
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=15, fill="x")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(padx=20, pady=10, fill="both")

    # ========================================================
    # دعم اللصق بزر الفأرة الأيمن
    # ========================================================
    def add_right_click(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    # ========================================================
    # تسجيل الرسائل
    # ========================================================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # ========================================================
    # ---------------- YouTube Downloader --------------------
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

    def select_by_size(self, max_mb):
        sorted_formats = sorted(self.formats, key=lambda x: x[2], reverse=True)
        for f in sorted_formats:
            if f[2] <= max_mb*1024*1024:
                return f
        return sorted_formats[-1] if sorted_formats else None

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
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                unique_path = unique_filename(filename)
                if unique_path != filename:
                    os.rename(filename, unique_path)
            self.log("Download finished.")
            self.open_folder()
        except Exception as e:
            self.log(f"Cancelled or Error: {e}")

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
    # ---------------- Video Compressor ----------------------
    # ========================================================

    def select_file(self):
        file = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")]
        )
        if file:
            self.selected_file = file
            self.file_entry.delete(0,"end")
            self.file_entry.insert(0,file)

    def get_video_duration(self, file):
        cmd = [
            FFMPEG.replace("ffmpeg.exe","ffprobe.exe"),
            "-v","error",
            "-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1",
            file
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
        duration = self.get_video_duration(self.selected_file)
        if duration == 0:
            self.log("Could not read duration.")
            return

        output = unique_filename(os.path.splitext(self.selected_file)[0] + "_compressed.mp4")
        target_size = self.target_size_entry.get().strip()

        # Smart CRF إذا لم يحدد حجم
        if not target_size:
            cmd = [
                FFMPEG,"-y",
                "-i",self.selected_file,
                "-c:v","libx264",
                "-crf","21",
                "-preset","medium",
                "-c:a","aac",
                "-b:a","128k",
                output
            ]
        else:
            try:
                size_mb = float(target_size)
                total_bits = size_mb*1024*1024*8
                audio_bitrate = 128000
                video_bitrate = int((total_bits/duration - audio_bitrate)/1000)
                cmd = [
                    FFMPEG,"-y",
                    "-i",self.selected_file,
                    "-c:v","libx264",
                    "-b:v",f"{video_bitrate}k",
                    "-preset","medium",
                    "-c:a","aac",
                    "-b:a","128k",
                    output
                ]
            except:
                self.log("Invalid target size.")
                return

        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8", errors="ignore")
        time_pattern = re.compile(r"time=(\d+:\d+:\d+\.\d+)")
        for line in process.stderr:
            if self.compress_cancel:
                process.kill()
                self.log("Compression cancelled.")
                return
            match = time_pattern.search(line)
            if match:
                h,m,s = match.group(1).split(":")
                current_time = float(h)*3600 + float(m)*60 + float(s)
                progress = current_time/duration
                self.progress.set(min(progress,1))
        process.wait()
        self.progress.set(1)
        self.log("Compression finished.")
        os.startfile(os.path.dirname(output))

    def cancel_compress(self):
        self.compress_cancel = True

    # ========================================================
    # فتح مجلد
    # ========================================================
    def open_folder(self):
        os.startfile(self.save_path)

# ============================================================
# تشغيل آمن
# ============================================================
if __name__=="__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        import traceback
        print("ERROR:", e)
        traceback.print_exc()
        input("Press Enter to exit...")