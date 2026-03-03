# ============================================================
#  Advanced Educational YouTube Downloader
# ============================================================
#
# ======================= الميزات ============================
#
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
# ============================================================

import os
import sys
import threading
import customtkinter as ctk
from tkinter import Menu
import yt_dlp

# ============================================================
# إعداد مظهر الواجهة
# ============================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ============================================================
# تحديد مسار ffmpeg (يدعم التشغيل كملف exe أو سكربت عادي)
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

        self.title("Eng. Abdul Baset Alsulaiman Educational YouTube Downloader")
        self.geometry("950x650")

        # مجلد الحفظ الافتراضي
        self.save_path = os.path.join(os.path.expanduser("~"), "Downloads")

        # تخزين الصيغ المتاحة
        self.formats = []

        # متغير إلغاء التحميل
        self.cancel_flag = False

        self.build_ui()

    # ========================================================
    # بناء الواجهة الرسومية
    # ========================================================
    def build_ui(self):

        ctk.CTkLabel(self,
                     text="YouTube Downloader",
                     font=("Arial", 24, "bold"),
                     text_color="#4da6ff").pack(pady=15)

        # إدخال الرابط
        self.url_entry = ctk.CTkEntry(self,
                                      placeholder_text="Paste YouTube URL")
        self.url_entry.pack(padx=20, fill="x")
        self.add_right_click(self.url_entry)

        # زر جلب الصيغ
        ctk.CTkButton(self,
                      text="Fetch Formats",
                      command=self.fetch_info).pack(pady=8)

        # قائمة الجودة
        self.quality_menu = ctk.CTkOptionMenu(self,
                                              values=["Select Quality"])
        self.quality_menu.pack(pady=5)

        # حجم أقصى اختياري
        self.size_entry = ctk.CTkEntry(self,
                                       placeholder_text="Max Size MB (Optional)")
        self.size_entry.pack(pady=5)

        # أزرار العمليات
        buttons = ctk.CTkFrame(self)
        buttons.pack(pady=10)

        ctk.CTkButton(buttons,
                      text="Download Video",
                      width=160,
                      command=self.start_video).grid(row=0, column=0, padx=5)

        ctk.CTkButton(buttons,
                      text="Download MP3 16kbps",
                      width=160,
                      command=self.start_mp3).grid(row=0, column=1, padx=5)

        ctk.CTkButton(buttons,
                      text="Cancel",
                      width=120,
                      fg_color="red",
                      command=self.cancel_download).grid(row=0, column=2, padx=5)

        # عرض مسار الحفظ
        self.path_label = ctk.CTkLabel(self,
                                       text=f"Save Path: {self.save_path}",
                                       text_color="#cccccc")
        self.path_label.pack(pady=5)

        # زر فتح المجلد
        ctk.CTkButton(self,
                      text="Open Download Folder",
                      command=self.open_folder).pack(pady=5)

        # شريط التقدم
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=15, fill="x")
        self.progress.set(0)

        # صندوق السجل
        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(padx=20, pady=10, fill="both")

    # ========================================================
    # دعم اللصق بزر الفأرة الأيمن
    # ========================================================
    def add_right_click(self, widget):
        menu = Menu(widget, tearoff=0)
        menu.add_command(label="Paste",
                         command=lambda: widget.event_generate("<<Paste>>"))
        widget.bind("<Button-3>",
                    lambda e: menu.tk_popup(e.x_root, e.y_root))

    # ========================================================
    # تسجيل الرسائل
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

        # دعم Playlist
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
        selected = next((f for f in self.formats
                         if f[0] == selected_label), None)

        max_size = self.size_entry.get().strip()
        if max_size:
            try:
                selected = self.select_by_size(float(max_size))
            except:
                pass

        format_string = (
            f"{selected[1]}+bestaudio/best"
            if selected else
            "bestvideo+bestaudio/best"
        )

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

    # ========================================================
    # إلغاء التحميل
    # ========================================================
    def cancel_download(self):
        self.cancel_flag = True
        self.log("Cancelling download...")

    # ========================================================
    # فتح مجلد التحميل
    # ========================================================
    def open_folder(self):
        os.startfile(self.save_path)

# ============================================================
# تشغيل آمن
# ============================================================
if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        import traceback
        print("ERROR:", e)
        traceback.print_exc()
        input("Press Enter to exit...")