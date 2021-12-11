# geotag_photos.py
Add GPS coordinates to non tagged EXIF taken with a DSLR Camera for example using your smartphone photos or Home Assistant DB
## Tag with Home Assistant DB - Example
python ./geotag_photos.py --db IP_DB_HASS PORT_DB_HASS DB_HASS DB_USER_HASS PWD_HASS --tz Europe/Paris --tag /Volumes/photo/2021_09\ Jardin\ d\'acclimatation/




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
