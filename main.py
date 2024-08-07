from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import yt_dlp

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. You can specify a list of allowed origins.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Get the current working directory
cur_dir = os.getcwd()

@app.get("/formats")
async def get_formats(link: str):
    """Endpoint to list available video formats in MP4 with quality information"""
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(link, download=False)
    
    formats = info.get('formats', [])
    format_dict = {}  # Dictionary to keep track of unique formats by quality
    
    for f in formats:
        if f.get('vcodec') and f.get('acodec') and f['ext'] == 'mp4':  # Ensure MP4 format and valid codecs
            quality = str(f.get('height', 'Unknown'))  # Get height if available and convert to string
            format_note = f.get('format_note', '')
            if format_note:
                quality += f" ({format_note})"
            
            format_id = f['format_id']
            if quality not in format_dict:
                format_dict[quality] = {
                    'format_id': format_id,
                    'quality': quality,
                    'ext': f['ext']
                }
    
    # Convert the dictionary values to a list for the response
    format_list = list(format_dict.values())
    
    return {"formats": format_list}

@app.post("/download")
async def download_video(link: str = Form(...), format_id: str = Form(...)):
    """Endpoint to download video in the selected MP4 format"""
    # Ensure the format_id is valid
    format_ext = 'mp4'
    
    # Generate a unique filename for the video to avoid overwriting
    filename = f"Video_{format_id}.{format_ext}"
    filepath = os.path.join(cur_dir, filename)
    
    youtube_dl_options = {
        "format": format_id,  # Selects the format based on format_id
        "outtmpl": filepath  # Save with the specified filename in the current directory
    }
    
    # Download the video
    with yt_dlp.YoutubeDL(youtube_dl_options) as ydl:
        ydl.download([link])
    
    # Return the video file as a response
    return FileResponse(filepath, media_type='video/mp4', filename=filename)
