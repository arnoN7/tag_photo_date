#!/usr/bin/python
import glob, os, sys
from datetime import date
from datetime import datetime
import pandas as pd
import os.path, time
import PIL.Image
import PIL.ExifTags
import piexif
import datefinder
import argparse
from tqdm import tqdm


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

def retag_date(file):
    # read the image data using PIL
    filename = os.path.basename(file)
    exif_dict = piexif.load(file)
    if piexif.ImageIFD.DateTime not in exif_dict['0th']:
        matches = datefinder.find_dates(filename)
        for match in matches:
            date_b = match.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict['0th'][piexif.ImageIFD.DateTime] = date_b
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_b
            exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_b
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, file)
    return True

def main():
    #try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--path', type=dir_path, required=True)
        parsed_args = parser.parse_args()
        os.chdir(parsed_args.path)
        i=0
        for file in tqdm(glob.glob("*.JPG")):
            i=i+1
            retag_date(file)
    #except:
        exc_type, exc_value, tb = sys.exc_info()
        if tb is not None:
            prev = tb
            curr = tb.tb_next
            while curr is not None:
                prev = curr
                curr = curr.tb_next
            print(prev.tb_frame.f_locals)


if __name__ == "__main__":
    main()

