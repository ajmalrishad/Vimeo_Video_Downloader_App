from vimeo_downloader import Vimeo

# Initialize Vimeo object with video URL
url = "https://vimeo.com/278398462"  # Replace with the actual video ID or URL
v = Vimeo(url)

# Get available video formats
video_formats = v.streams

# Print available video formats
print("This is are the available video formats:")
for stream in video_formats:
    print(stream.quality)

# Choose a format (e.g., '720p')
chosen_format = "1080p"

# Find the stream with the chosen format
chosen_stream = None
for stream in video_formats:
    if stream.quality == chosen_format:
        chosen_stream = stream
        break

# Download the video
if chosen_stream:
    chosen_stream.download()
    print("Video downloaded successfully!")
else:
    print("Error in video download or Chosen format not available.")