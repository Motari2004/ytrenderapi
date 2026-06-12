from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import tempfile
import os
import re
import uuid
import base64

app = Flask(__name__)
CORS(app)

def get_cookies_file():
    """Get cookies from environment variable or secret file"""
    if os.path.exists('/app/cookies.txt'):
        return '/app/cookies.txt'
    
    cookies_base64 = os.environ.get('YOUTUBE_COOKIES_BASE64', '')
    if cookies_base64:
        try:
            cookies_path = '/tmp/cookies.txt'
            cookies_content = base64.b64decode(cookies_base64).decode('utf-8')
            with open(cookies_path, 'w') as f:
                f.write(cookies_content)
            print("✅ Loaded cookies from environment variable")
            return cookies_path
        except Exception as e:
            print(f"⚠️ Failed to decode cookies: {e}")
    
    if os.path.exists('/etc/secrets/cookies.txt'):
        return '/etc/secrets/cookies.txt'
    
    print("⚠️ No cookies found")
    return None

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([a-zA-Z0-9_-]{11})',
        r'youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'embed\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/health', methods=['GET'])
def health():
    cookies_available = get_cookies_file() is not None
    return jsonify({
        'status': 'healthy', 
        'message': 'API is running',
        'cookies_loaded': cookies_available
    })

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    print(f"Downloading: {url}")
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    temp_filename = f"/tmp/video_{uuid.uuid4().hex}.mp4"
    cookies_file = get_cookies_file()
    
    # Try multiple formats in order of preference
    formats_to_try = [
        'best[ext=mp4]',
        'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        '22',  # 720p MP4
        '18',  # 360p MP4
        'best'
    ]
    
    for format_spec in formats_to_try:
        try:
            print(f"Trying format: {format_spec}")
            
            ydl_opts = {
                'outtmpl': temp_filename,
                'format': format_spec,
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                    }
                }
            }
            
            if cookies_file:
                ydl_opts['cookiefile'] = cookies_file
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                safe_title = re.sub(r'[^\w\s.-]', '', title)[:50]
                filename = f"{safe_title}.mp4"
                
                print(f"✅ Downloaded with format {format_spec}: {filename}")
                
                return send_file(
                    temp_filename,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='video/mp4'
                )
                
        except Exception as e:
            print(f"Format {format_spec} failed: {e}")
            continue
        finally:
            # Clean up temp file if it exists
            try:
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
            except:
                pass
    
    return jsonify({'error': 'No valid format found for this video'}), 500

@app.route('/info', methods=['GET'])
def info():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    cookies_file = get_cookies_file()
    
    try:
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        if cookies_file:
            ydl_opts['cookiefile'] = cookies_file
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get available formats
            formats = []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution'),
                        'filesize': f.get('filesize')
                    })
            
            return jsonify({
                'success': True,
                'title': info.get('title'),
                'duration': info.get('duration'),
                'thumbnail': info.get('thumbnail'),
                'video_id': video_id,
                'formats': formats[:5]
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}")
    cookies_available = get_cookies_file() is not None
    print(f"🍪 Cookies available: {cookies_available}")
    app.run(host='0.0.0.0', port=port, debug=False)