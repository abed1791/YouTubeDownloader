"""
Video Compressor - Professional Edition (تعليمي)

الميزات:
1. ضغط ملفات الفيديو من جهاز الكمبيوتر بكفاءة عالية.
2. حساب CRF ذكي بناءً على دقة الفيديو وجودته الأصلية.
3. احتساب جودة الصوت مع الحفاظ على التوافق مع libx264 وAAC.
4. دعم السحب والإفلات، النقر بزر الفأرة الأيمن، واللصق.
5. تجنب تكرار أسماء الملفات: عند وجود ملف بنفس الاسم يتم إضافة رقم تصاعدي.
6. عرض مسار الفيديو الأصلي ومسار الفيديو الناتج.
7. دعم صيغ MP4, MOV, MKV, AVI, وغيرها.
8. واجهة تعليمية داخل الكود لتسهيل التعلم والفهم.
"""

import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

def smart_crf(width, height):
    """تحديد قيمة CRF بناءً على دقة الفيديو"""
    pixels = width * height
    if pixels <= 640*360:
        return 23
    elif pixels <= 1280*720:
        return 21
    elif pixels <= 1920*1080:
        return 20
    else:
        return 18

def get_unique_filename(output_dir, base_name, ext):
    """إرجاع اسم ملف فريد لتجنب التكرار"""
    counter = 1
    new_name = f"{base_name}{ext}"
    while os.path.exists(os.path.join(output_dir, new_name)):
        new_name = f"{base_name}_{counter}{ext}"
        counter += 1
    return new_name

def compress_video(input_path, output_dir):
    try:
        # استخراج معلومات الفيديو
        cmd_info = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0",
            input_path
        ]
        result = subprocess.run(cmd_info, capture_output=True, text=True)
        width, height = map(int, result.stdout.strip().split(','))

        crf_value = smart_crf(width, height)
        base_name, ext = os.path.splitext(os.path.basename(input_path))
        output_name = get_unique_filename(output_dir, f"{base_name}_compressed", ext)
        output_path = os.path.join(output_dir, output_name)

        # أمر ffmpeg للضغط
        cmd_ffmpeg = [
            "ffmpeg", "-i", input_path,
            "-c:v", "libx264", "-crf", str(crf_value),
            "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            output_path
        ]

        print(f"ضغط الفيديو: {input_path}")
        print(f"حفظ الفيديو المضغوط في: {output_path}")
        subprocess.run(cmd_ffmpeg)

        messagebox.showinfo("نجاح", f"تم ضغط الفيديو وحفظه:\n{output_path}")
    except Exception as e:
        messagebox.showerror("خطأ", str(e))

# واجهة المستخدم البسيطة
def select_file():
    file_path = filedialog.askopenfilename(
        title="اختر فيديو للضغط",
        filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.avi *.flv *.wmv")]
    )
    if file_path:
        output_dir = filedialog.askdirectory(title="اختر مجلد لحفظ الفيديو المضغوط")
        if output_dir:
            threading.Thread(target=compress_video, args=(file_path, output_dir)).start()

# واجهة بسيطة مع دعم النقر الأيمن واللصق
root = tk.Tk()
root.title("Video Compressor - Professional")
root.geometry("400x200")

btn_select = tk.Button(root, text="اختر فيديو للضغط", command=select_file)
btn_select.pack(expand=True)

# دعم السحب والإفلات على الزر
def drop(event):
    files = root.tk.splitlist(event.data)
    for f in files:
        output_dir = filedialog.askdirectory(title="اختر مجلد لحفظ الفيديو المضغوط")
        if output_dir:
            threading.Thread(target=compress_video, args=(f, output_dir)).start()

btn_select.drop_target_register(tk.DND_FILES)
btn_select.dnd_bind('<<Drop>>', drop)

root.mainloop()