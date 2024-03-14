import requests
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
from vimeo_downloader import Vimeo
import os

class VideoDownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("Vimeo Video Downloader")

        self.label_empty = tk.Label(master, text="")
        self.label_empty.pack(pady=50)

        self.url_label_text = tk.Label(master, text="Enter Vimeo Video URL:")
        self.url_label_text.pack(padx=10, pady=10)

        self.url_entry = tk.Entry(master, width=50)
        self.url_entry.pack(padx=10, pady=10)
        # Bind right-click context menu to the entry widget
        self.url_entry.bind("<Button-3>", self.show_menu)

        self.process_button = tk.Button(master, text="PROCESS", bg="#3b71ca", fg="white", command=self.process_video, font=('Helvetica', 10))
        self.process_button.pack()

        self.resolution_var = tk.StringVar(master)  # Initialize resolution variable

        self.downloading = False  # Flag to track if download is in progress

    def show_menu(self, event):
        # Create a right-click context menu
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="Paste", command=lambda: self.url_entry.event_generate('<<Paste>>'))
        menu.tk_popup(event.x_root, event.y_root)

    def process_video(self):
        url = self.url_entry.get().strip()
        startwith = url.startswith('https://vimeo.com/')
        if url and startwith:
            if url and not self.downloading:  # Check if URL is valid and no download in progress
                self.master.withdraw()  # Hide the main window
                self.show_success_page(url)
            elif self.downloading:
                messagebox.showinfo("Download in Progress", "A download is already in progress. Please wait until it completes.")
            else:
                messagebox.showerror("Error", "No video URL found.")
        else:
            messagebox.showerror("Error", "Please enter a valid video URL.")

    def show_success_page(self, url):
        success_window = tk.Toplevel(self.master)
        # Set geometry to match main window
        success_window.geometry(self.master.geometry())

        thumbnail_url = self.get_vimeo_thumbnail(url)
        if thumbnail_url:
            response = requests.get(thumbnail_url)
            image_bytes = BytesIO(response.content)
            img = Image.open(image_bytes)
            img = img.resize((300, 200), Image.LANCZOS)  # Use LANCZOS instead of ANTIALIAS
            img = ImageTk.PhotoImage(img)

            thumbnail_label = tk.Label(success_window, image=img)
            thumbnail_label.image = img
            thumbnail_label.pack(pady=10)

        video_id = url.split('/')[-1]
        response = requests.get(f"https://vimeo.com/api/v2/video/{video_id}.json")
        if response.status_code == 200 and response.headers['Content-Type'] == 'application/json':
            video_data = response.json()[0]
            video_title = video_data['title']
            success_window.title("Vimeo Video Download")
            success_window.iconbitmap(r'vimeo.ico')
            self.video_name_label = tk.Label(success_window, text="Video Name: "f'{video_title}')
            self.video_name_label.pack(pady=10)
        else:
            self.video_name_label = tk.Label(success_window, text="Video Name: Not available")
            self.video_name_label.pack(pady=10)

        # Get available resolutions
        resolutions = self.get_available_resolutions(url)

        # Choose the highest available quality as default
        chosen_format = resolutions[-1] if resolutions else None

        # Update resolution dropdown menu with available resolutions
        self.video_resolution_label = tk.Label(success_window, text="Select Video Resolution :")
        self.video_resolution_label.pack()

        if resolutions:
            self.resolution_var.set(chosen_format)
            resolution_dropdown = tk.OptionMenu(success_window, self.resolution_var, *resolutions)
            resolution_dropdown.pack(pady=10)

             # Download button
            download_button = tk.Button(success_window, text="Download", bg="green", fg="white", command=lambda: self.download_video(url, success_window))
            download_button.pack()
        else:
            no_resolution_label = tk.Label(success_window, text="No resolutions available for this video")
            no_resolution_label.pack(pady=10)

            retry = tk.Button(success_window, text="Retry", bg="red", fg="white", command=lambda: self.retry(success_window))
            retry.pack()

    def retry(self, success_window):
        success_window.destroy()  # Close the success window
        self.master.deiconify()   # Show the master window

    def get_vimeo_thumbnail(self, url):
        video_id = url.split('/')[-1]
        response = requests.get(f"https://vimeo.com/api/v2/video/{video_id}.json")

        if response.status_code == 200 and response.headers['Content-Type'] == 'application/json':
            video_data = response.json()
            thumbnail_url = video_data[0]['thumbnail_large']
            return thumbnail_url
        else:
            print(f"Failed to fetch thumbnail for video: {url}")
            messagebox.showerror("Error", f"Failed to fetch thumbnail for this URL: {url}")
            return None

    def get_available_resolutions(self, url):
        try:
            v = Vimeo(url)
            video_formats = v.streams
            resolutions = [stream.quality for stream in video_formats]
            print("These are the available video formats:")
            for stream in video_formats:
                print(stream.quality)
            return resolutions
        except Exception as e:
            messagebox.showerror("Error", f"Unable to retrieve download links: {str(e)}")

    def download_video(self, url, success_window):
        if not self.downloading == True:
            self.downloading = True  # Set downloading flag to True
            self.process_button.config(state='disabled')  # Disable the download button

            download_thread = threading.Thread(target=self.download_video_thread, args=(url, success_window))
            download_thread.start()
        else:
            messagebox.showwarning("Downloading video","video download in progress please wait....")

    def download_video_thread(self, url, success_window):
        try:
            v = Vimeo(url)
            video_formats = v.streams

            # Get selected resolution
            chosen_format = self.resolution_var.get()
            print("Choosen video format:", chosen_format)

            # Choose the highest available quality if no resolution selected
            if not chosen_format:
                chosen_format = video_formats[-1].quality if video_formats else None
                
            # Download the video
            chosen_stream = next((stream for stream in video_formats if stream.quality == chosen_format), None)
            if chosen_stream:
                try:
                    # Create a label for download video status
                    self.downloadstatus = tk.Label(success_window, fg="green", text="Downloading...")
                    self.downloadstatus.pack(pady=10)

                    # Create progress bar
                    self.progress_bar = ttk.Progressbar(success_window, mode='determinate')
                    self.progress_bar.pack()
            
                    self.progress_bar.start()  # Start the progress bar
                    file_path = chosen_stream.download()
                    self.progress_bar.stop()  # Stop the progress bar
                    self.progress_bar.pack_forget()  # Hide the progress bar
                    self.downloadstatus.pack_forget() # Hide the download status
                    print("Video downloaded successfully!")
                    # Append chosen format to the file name
                    file_name, file_extension = os.path.splitext(file_path)
                    new_file_path = f"{file_name}_{chosen_format}{file_extension}"
                    # Check if the file already exists
                    if os.path.exists(new_file_path):
                        # If the file exists, overwrite it
                        os.replace(file_path, new_file_path)
                    else:
                        # If the file doesn't exist, rename it
                        os.rename(file_path, new_file_path)
                    messagebox.showinfo("Download Successful", "Video downloaded successfully!")
                    self.master.deiconify()  # Show the main window again after download
                    self.process_button.config(state='normal')
                    # Hide the success window and destroy it
                    success_window.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Unable to download: {str(e)}")
                    self.master.deiconify()  # Show the main window again after download
                    success_window.destroy()
            else:
                messagebox.showerror("Error", "Error in video download or video resolution not available for this video")
                success_window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Unable to retrieve download links or error due to so many requests please try again later: {str(e)}")
        # Reset downloading flag after download completes
        self.downloading = False


def main():
    root = tk.Tk()
    root.iconbitmap(r'vimeo.ico')
    root.minsize(500, 500)
    app = VideoDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
