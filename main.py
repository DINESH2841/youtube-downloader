from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import yt_dlp
from celery import Celery
import time

# Flask App initialization
app = Flask(__name__)

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Function to download the video (in the background)
@celery.task(bind=True)
def download_video_task(self, url):
    self.update_state(state='PROGRESS', meta={'status': 'Downloading started...'})
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return {'status': 'Download completed successfully!'}
    except Exception as e:
        return {'status': f'Error: {str(e)}'}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form['video_url']
        task = download_video_task.apply_async(args=[video_url])  # Trigger background task
        return redirect(url_for('download_status', task_id=task.id))  # Redirect to the status page
    return render_template('index.html', message='')

@app.route('/status/<task_id>')
def download_status(task_id):
    task = download_video_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'state': task.state,
            'status': str(task.info)  # Error message
        }
    return jsonify(response)

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(debug=True)
