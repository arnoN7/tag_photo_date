# geotag_photos.py
Add GPS coordinates to non tagged EXIF taken by a DSLR Camera for example using your smartphone photos or Home Assistant DB
## Tag with Home Assistant DB - Example

python ./src/geotag_photos.py --tz Europe/Paris --tag ./photos

.venv should be defined in the same folder as the script with the following content
```
# Database Configuration
DB_HOST=[HOST_IP]
DB_PORT=[HOST_PORT]
DB_NAME=[DATABASE_NAME]
DB_USER=[DATABASE_USER]
DB_PASSWORD=[DATABASE_PASSWORD]
```



# tag_photo_date
Enrich EXIF with dates based on the image file name
Supported formats :
- IMG-20170412-WA0004.jpg
- Screenshot_2016-04-12-21-17-46.jpg
- 2013-12-03 19.23.48.jpg
- 20150420_202551-1.jpg
- 20160504_150820.jpg

usage: retag_dates.py [-h] --path PATH

optional arguments:
  -h, --help   show this help message and exit
  --path PATH  path to the folder with photos to tag
