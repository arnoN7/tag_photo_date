import os
from datetime import datetime, timedelta
import piexif
from PIL import Image

def update_exif_time(photo_path, hours_to_add=1):
    try:
        exif_dict = piexif.load(photo_path)
        original_time_bytes = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)

        if original_time_bytes:
            original_time_str = original_time_bytes.decode("utf-8")
            original_time = datetime.strptime(original_time_str, "%Y:%m:%d %H:%M:%S")

            # Add 1 hour
            new_time = original_time + timedelta(hours=hours_to_add)
            new_time_str = new_time.strftime("%Y:%m:%d %H:%M:%S")
            new_time_bytes = new_time_str.encode("utf-8")

            # Update all relevant EXIF tags
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = new_time_bytes
            exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = new_time_bytes
            exif_dict["0th"][piexif.ImageIFD.DateTime] = new_time_bytes

            # Save back
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, photo_path)

            print(f"✅ Updated {photo_path} to {new_time_str}")
        else:
            print(f"⚠️ No DateTimeOriginal in {photo_path}")

    except Exception as e:
        print(f"❌ Failed to process {photo_path}: {e}")

def update_folder_exif(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".jpg", ".jpeg")):
            full_path = os.path.join(folder_path, filename)
            update_exif_time(full_path)

if __name__ == "__main__":
    folder = './2025_04 Romania Paste'  
    update_folder_exif(folder)
