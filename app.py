import os
import uuid
from datetime import timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

# ایجاد پوشه‌های مورد نیاز اگر وجود ندارند
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

def get_video_duration(filepath):
    """دریافت مدت زمان ویدیو"""
    try:
        with VideoFileClip(filepath) as video:
            return video.duration
    except Exception as e:
        print(f"Error getting video duration: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        file_extension = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{unique_id}.{file_extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(filepath)
        
        duration = get_video_duration(filepath)
        if duration is None:
            os.remove(filepath)
            return jsonify({'error': 'Invalid video file'}), 400
        
        duration_formatted = format_timedelta(timedelta(seconds=duration))
        
        return jsonify({
            'success': True,
            'filename': new_filename,
            'duration': duration,
            'duration_formatted': duration_formatted
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/cut', methods=['POST'])
def cut_video():
    data = request.get_json()
    filename = data.get('filename')
    start_min = float(data.get('start_min', 0))
    end_min = float(data.get('end_min', 0))
    
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400
    
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # تبدیل دقیقه به ثانیه
        start_time = start_min * 60
        end_time = end_min * 60
        
        # بررسی محدوده زمانی
        duration = get_video_duration(input_path)
        if end_time > duration:
            end_time = duration
        if start_time >= end_time:
            return jsonify({'error': 'Invalid time range'}), 400
        
        # ایجاد نام فایل خروجی
        output_filename = f"cut_{start_min}_{end_min}_{filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # برش ویدیو با moviepy
        with VideoFileClip(input_path) as video:
            cut_video = video.subclip(start_time, end_time)
            cut_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                threads=4  # استفاده از چند هسته برای پردازش سریعتر
            )
        
        return jsonify({
            'success': True,
            'cut_filename': output_filename,
            'start_time': format_timedelta(timedelta(seconds=start_time)),
            'end_time': format_timedelta(timedelta(seconds=end_time))
        })
    
    except Exception as e:
        print(f"Error cutting video: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """پاکسازی فایل‌های موقت"""
    try:
        for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
