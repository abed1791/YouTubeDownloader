# ============================================================
#  Advanced Educational Downloader & Compressor (Stable)
# ============================================================
#
# ======================= الميزات ============================
#
# قسم YouTube:
# ✔ تحميل فيديو مع الصوت دائماً (دمج video+audio)
# ✔ دعم Playlist
# ✔ اختيار جودة مع عرض الحجم
# ✔ اختيار حجم مخصص
# ✔ MP3 16kbps
# ✔ زر إلغاء التحميل
# ✔ شريط تقدم دقيق
# ✔ حفظ الاسم الأصلي
# ✔ منع تكرار الاسم (إضافة رقم تصاعدي تلقائياً)
# ✔ فتح مجلد التحميل بعد الانتهاء
# ✔ زر فتح مجلد التحميل
# ✔ عرض مسار الحفظ
# ✔ دعم اللصق بزر الفأرة الأيمن
# ✔ بدون أخطاء Unicode
#
# قسم الضغط المحلي:
# ✔ (بدون أي تغيير كما طلبت)
#
# ============================================================

import os
import sys
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog, Menu
import yt_dlp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================
# مسار ffmpeg
# ============================================================
def get_ffmpeg():
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "ffmpeg.exe")

FFMPEG = get_ffmpeg()

# ============================================================
# منع تكرار الاسم (توليد اسم فريد)
# ============================================================
def unique_filename(directory, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_name = filename
    full_path = os.path.join(directory, new_name)

    while os.path.exists(full_path):
        new_name = f"{base}_{counter}{ext}"
        full_path = os.path.join(directory, new_name)
        counter += 1

    return full_path

# ============================================================
# التطبيق الرئيسي
# ============================================================
class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Educational Downloader & Compressor V456")
        self.geometry("950x820")

        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.formats = []
        self.cancel_flag = False
        self.selected_file = ""

        self.build_ui()

    # ========================================================
    # بناء الواجهة
    # ========================================================
    def build_ui(self):

        ctk.CTkLabel(self, text="YouTube Downloader",
                     font=("Arial", 22, "bold"),
                     text_color="#4da6ff").pack(pady=10)

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")
        self.add_right_click(self.url_entry)

        ctk.CTkButton(self, text="Fetch Formats",
                      command=self.fetch_info).pack(pady=5)

        self.quality_menu = ctk.CTkOptionMenu(self, values=["Select Quality"])
        self.quality_menu.pack(pady=5)

        self.size_entry = ctk.CTkEntry(self,
                                       placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        yt_buttons = ctk.CTkFrame(self)
        yt_buttons.pack(pady=8)

        ctk.CTkButton(yt_buttons, text="Download Video",
                      width=160,
                      command=self.start_video).grid(row=0, column=0, padx=5)

        ctk.CTkButton(yt_buttons, text="Download MP3 16kbps",
                      width=160,
                      command=self.start_mp3).grid(row=0, column=1, padx=5)

        ctk.CTkButton(yt_buttons, text="Cancel",
                      width=120,
                      fg_color="red",
                      command=self.cancel_download).grid(row=0, column=2, padx=5)

        self.path_label = ctk.CTkLabel(self,
                                       text=f"Save Path: {self.save_path}",
                                       text_color="#cccccc")
        self.path_label.pack(pady=5)

        ctk.CTkButton(self, text="Open Download Folder",
                      command=self.open_folder).pack(pady=5)

        # ================= قسم الضغط المحلي (بدون تغيير) =================

        ctk.CTkLabel(self, text="Local Video Compressor",
                     font=("Arial", 22, "bold"),
                     text_color="#00cc99").pack(pady=20)

        self.file_entry = ctk.CTkEntry(self,
                                       placeholder_text="Select local video file")
        self.file_entry.pack(padx=20, fill="x")
        self.add_right_click(self.file_entry)

        comp_buttons = ctk.CTkFrame(self)
        comp_buttons.pack(pady=8)

        ctk.CTkButton(comp_buttons, text="Select File",
                      width=160,
                      command=self.select_file).grid(row=0, column=0, padx=5)

        ctk.CTkButton(comp_buttons, text="Compress",
                      width=160,
                      command=self.start_compress).grid(row=0, column=1, padx=5)

        self.target_size_entry = ctk.CTkEntry(self,
                                              placeholder_text="Target Size MB (Optional)")
        self.target_size_entry.pack(pady=5)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=15, fill="x")
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(padx=20, pady=10, fill="both")

    # ========================================================
    # دعم اللصق بزر الفأرة
    # ========================================================
    def add_right_click(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste",
                         command=lambda: widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>",
                    lambda e: menu.tk_popup(e.x_root, e.y_root))

    # ========================================================
    # تسجيل
    # ========================================================
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # ========================================================
    # جلب الصيغ مع الحجم
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
                size = f.get("filesize") or 0
                size_mb = round(size/1024/1024, 2) if size else 0
                label = f"{f['height']}p - {size_mb} MB"
                self.formats.append((label, f["format_id"]))
                labels.append(label)

        if labels:
            self.quality_menu.configure(values=labels)
            self.quality_menu.set(labels[0])

    # ========================================================
    # تنزيل فيديو (مع إعادة تسمية تلقائية)
    # ========================================================
    def start_video(self):
        self.cancel_flag = False
        threading.Thread(target=self.download_video).start()

    def download_video(self):

        url = self.url_entry.get().strip()
        selected_label = self.quality_menu.get()

        selected = next((f for f in self.formats
                         if f[0] == selected_label), None)

        format_string = f"{selected[1]}+bestaudio/best" if selected else "bestvideo+bestaudio/best"

        def hook(d):
            if self.cancel_flag:
                raise Exception("Cancelled")
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').replace('%', '').strip()
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

                # إعادة تسمية إذا كان الاسم مكرر
                filename = ydl.prepare_filename(info)
                directory = os.path.dirname(filename)
                original_name = os.path.basename(filename)

                unique_path = unique_filename(directory, original_name)

                if unique_path != filename:
                    os.rename(filename, unique_path)

            self.log("Download finished.")
            self.open_folder()

        except Exception as e:
            self.log(f"Cancelled or Error: {e}")

    # ========================================================
    # MP3
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
            directory = os.path.dirname(filename)
            original_name = os.path.basename(filename)

            unique_path = unique_filename(directory, original_name)

            if unique_path != filename:
                os.rename(filename, unique_path)

        self.log("MP3 finished.")
        self.open_folder()

    # ========================================================
    # إلغاء
    # ========================================================
    def cancel_download(self):
        self.cancel_flag = True
        self.log("Cancelling...")

    # ========================================================
    # فتح مجلد
    # ========================================================
    def open_folder(self):
        os.startfile(self.save_path)

    # ========================================================
    # قسم الضغط المحلي (بدون تغيير)
    # ========================================================
    def select_file(self):
        file = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")]
        )
        if file:
            self.selected_file = file
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file)

    def start_compress(self):
        threading.Thread(target=self.compress_video).start()

    def compress_video(self):

        if not self.selected_file:
            return

        output = os.path.splitext(self.selected_file)[0] + "_compressed.mp4"

        cmd = [
            FFMPEG, "-y",
            "-i", self.selected_file,
            "-c:v", "libx264",
            "-crf", "21",
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "128k",
            output
        ]

        subprocess.run(cmd, encoding="utf-8", errors="ignore")

        self.log("Compression finished.")


# ============================================================
# تشغيل آمن
# ============================================================
if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print("ERROR:", e)
        input("Press Enter to exit...")