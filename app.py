from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
import os
from uuid import uuid4
from datetime import timedelta

app = Flask(__name__)

# تنظیمات
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'flv'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

# ایجاد پوشه‌ها اگر وجود ندارند
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def format_timedelta(td):
    """تبدیل timedelta به فرمت HH:MM:SS"""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(original_path)
        
        # دریافت اطلاعات ویدیو
        try:
            with VideoFileClip(original_path) as video:
                duration = video.duration
                formatted_duration = format_timedelta(timedelta(seconds=duration))
                fps = video.fps
                width, height = video.size
                
            return render_template('video_info.html', 
                                 filename=filename,
                                 unique_id=unique_id,
                                 duration=duration,
                                 formatted_duration=formatted_duration,
                                 fps=fps,
                                 resolution=f"{width}x{height}")
        except Exception as e:
            os.remove(original_path)
            return f"خطا در پردازش ویدیو: {str(e)}"
    
    return redirect(request.url)

@app.route('/cut', methods=['POST'])
def cut_video():
    unique_id = request.form['unique_id']
    original_filename = request.form['original_filename']
    start_min = float(request.form['start_min'])
    end_min = float(request.form['end_min'])
    
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{original_filename}")
    output_filename = f"cut_{start_min}_{end_min}_{original_filename}"
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    
    try:
        # تبدیل دقیقه به ثانیه
        start_sec = start_min * 60
        end_sec = end_min * 60
        
        with VideoFileClip(original_path) as video:
            # برش ویدیو
            cut_video = video.subclip(start_sec, end_sec)
            cut_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        return render_template('download.html', 
                             filename=output_filename,
                             original_filename=original_filename,
                             start_min=start_min,
                             end_min=end_min)
    except Exception as e:
        return f"خطا در برش ویدیو: {str(e)}"

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

@app.route('/cleanup', methods=['POST'])
def cleanup():
    try:
        # حذف فایل‌های موقت
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.remove(file_path)
        
        for filename in os.listdir(app.config['PROCESSED_FOLDER']):
            file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
            os.remove(file_path)
            
        return "تمامی فایل‌ها با موفقیت پاک شدند."
    except Exception as e:
        return f"خطا در پاکسازی فایل‌ها: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
