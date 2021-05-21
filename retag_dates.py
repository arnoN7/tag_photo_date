#!/usr/bin/python
import glob, os, sys
from datetime import datetime, timedelta
import os.path
import piexif
import argparse
from tqdm import tqdm
import re
from geotag_photos import get_file_date
from utils import dir_path
from geotag_photos import FORMAT

MODIFIED_FILES = 0
NO_MATCH_FILES = 0
INCONSISTENT_EXIF = 0

def try_parsing_date(text):
    for fmt in [['IMG-\d+-WA','IMG-%Y%m%d-WA'], ['\d+-\d+-\d+ \d+.\d+.\d+', '%Y-%m-%d %H.%M.%S'], ['\d+_\d+', '%Y%m%d_%H%M%S'], ['Screenshot_\d+-\d+','Screenshot_%Y%m%d-%H%M%S']]:
        try:
            text_extract = re.findall(fmt[0],text)
            if (len(text_extract)>0):
                return datetime.strptime(text_extract[0], fmt[1])
        except ValueError:
            pass
    print('no valid date format found for ' + text)
    global NO_MATCH_FILES
    NO_MATCH_FILES = NO_MATCH_FILES + 1
    return None

def retag_date(file):
    filename = os.path.basename(file)
    exif_dict = piexif.load(file)
    if piexif.ImageIFD.DateTime not in exif_dict['0th']:
        date_file_name = try_parsing_date(file)
        if date_file_name is not None:
            date_b = date_file_name.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict['0th'][piexif.ImageIFD.DateTime] = date_b
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_b
            exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_b
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, file)
            global MODIFIED_FILES
            MODIFIED_FILES = MODIFIED_FILES + 1
    else:
        try:
            #catch dates not well formated
            old_date_b = exif_dict['0th'][piexif.ImageIFD.DateTime]
            old_date = datetime.strptime(old_date_b.decode("utf-8"), '%Y:%m:%d %H:%M:%S')
        except ValueError:
            piexif.remove(file)
            global INCONSISTENT_EXIF
            INCONSISTENT_EXIF = INCONSISTENT_EXIF + 1
            print('Invalid date format in EXIF found for ' + file)
            retag_date(file)
            pass

    return True


def delay_date(file, offset):
    filename = os.path.basename(file)
    exif_dict = piexif.load(file)
    init_date = datetime.strptime(get_file_date(file, False), FORMAT)
    print('init-date' + init_date.strftime(FORMAT))
    date_target = init_date - timedelta(hours=-1)
    print('Init date ' + get_file_date(file, False) + 'New Date ' + date_target.strftime(FORMAT))
    if date_target is not None:
        date_b = date_target.strftime("%Y:%m:%d %H:%M:%S")
        exif_dict['0th'][piexif.ImageIFD.DateTime] = date_b
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_b
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_b
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file)
        global MODIFIED_FILES
        MODIFIED_FILES = MODIFIED_FILES + 1



def main():
    #try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--path', type=dir_path, required=True, help='path to the folder with photos to tag')
        parser.add_argument("-o", "--offset", dest="offset", type=int,
                    help="Hours to delay")
        parsed_args = parser.parse_args()
        os.chdir(parsed_args.path)
        i=0
        for file in tqdm(glob.glob("*.JP*G")):
            i=i+1
            if parsed_args.offset is not None:
                delay_date(file, parsed_args.offset)
            else:
                retag_date(file)
        print(str(MODIFIED_FILES) + ' files enriched with dates ')
        print(str(NO_MATCH_FILES) + ' files not updated due to file format error ')
        print(str(INCONSISTENT_EXIF) + ' files updated because of date format error in original EXIF ')
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

