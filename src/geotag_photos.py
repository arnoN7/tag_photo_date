import glob, os, sys, time
import pandas as pd
import piexif
from datetime import datetime
import logging
import logging.config
import argparse
from utils import dir_path

log_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file_handler': {
            'level': 'INFO',
            'filename': 'app.log',
            'class': 'logging.FileHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {
            'handlers': ['file_handler', 'default'],
            'propagate': True,
            'level': 'INFO'
        },
    }
}
logging.config.dictConfig(log_dict)

#logging.config.fileConfig('logging.conf')
# create logger
#logger = logging.getLogger(__name__)


DIR_TO_TAG = "/Users/administrateur/Pictures/testgeotag/totag"
closest_tag_file =""
FORMAT='%Y-%m-%d %H:%M:%S'
EXIF_FORMAT='%Y:%m:%d %H:%M:%S'
df = pd.DataFrame()
d = []
NB_TAGGED_FILE = 0
NB_NOT_TAGGED_FILE = 0
NB_ALREADY_TAGGED_FILE = 0
SECONDS_PER_DAY = 24 * 60 * 60
MAX_DELAY = 1.0

def nearest_tagged_file(non_tagged_file):
    global df
    dt = pd.to_datetime(get_file_date(non_tagged_file, False), format=FORMAT)
    if dt is not None:
        return (df.loc[(pd.to_datetime(df['DATE'])
                          - dt).abs().idxmin(),'FILE'])
    else:
        return None


def load_tagged_folder(folders):
    d = []
    global df
    for folder in folders:
        logging.info('       %i/%i = Loading folder %s', folders.index(folder) + 1, len(folders), folder)
        os.chdir(folder)
        for file in tqdm(glob.glob("*.JP*G") + glob.glob("*.jp*g")):
            date = get_file_date(os.path.join(folder, file), True)
            if date is not None:
                d.append(
                    {
                        'FILE': os.path.join(folder, file),
                        'DATE': get_file_date(file, True)
                    }
                )
    df = pd.DataFrame(d)
    df.DATE = pd.to_datetime(df.DATE, format=FORMAT)
    return True


def get_file_date(file, checkGPS):
    exif_dict = piexif.load(file)
    if piexif.ImageIFD.DateTime not in exif_dict['0th']:
        logging.debug('No Date for ' + file)
        return None
    else:
        try:
            date_b = exif_dict['0th'][piexif.ImageIFD.DateTime]
            if checkGPS:
                if (1 not in exif_dict['GPS']):
                    logging.debug('No GPS found for ' + file)
                    logging.debug(exif_dict['GPS'])
                    return None
            return datetime.strptime(date_b.decode("utf-8"), '%Y:%m:%d %H:%M:%S').strftime(FORMAT)
        except ValueError:
            logging.debug('Invalid date format in EXIF found for ' + file + ' date found : '+ date_b.decode("utf-8"))
            return None


def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

def assign_geotag_from_file(file, tagged_file):
    exif_dict_tagged = piexif.load(tagged_file)
    exif_dict = piexif.load(file)
    if (1 in exif_dict['GPS']):
        global NB_ALREADY_TAGGED_FILE
        NB_ALREADY_TAGGED_FILE = NB_ALREADY_TAGGED_FILE + 1
        logging.debug('File %s ignored already GPS Tagged ', file)
        return False
    if (1 not in exif_dict_tagged['GPS']):
        global NB_NOT_TAGGED_FILE
        NB_NOT_TAGGED_FILE = NB_NOT_TAGGED_FILE + 1
        logging.debug(' %s ignored no GPS Tag in GPS file %s', file, tagged_file)
        return False
    exif_dict['GPS'] = exif_dict_tagged['GPS']
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, file)
    logging.debug('%s file tagged with GPS File %s', file, tagged_file)
    global NB_TAGGED_FILE
    NB_TAGGED_FILE = NB_TAGGED_FILE + 1
    return True

def tag_photo(file):
    if file is not None:
        gps_file = nearest_tagged_file(file)
        if gps_file is not None:
            date_gps = datetime.strptime(get_file_date(gps_file, False), FORMAT)
            date_file = datetime.strptime(get_file_date(file, False), FORMAT)
            if date_gps is not None:
                if date_file is not None:
                    delay = abs((date_file - date_gps).total_seconds())
                    if delay < (SECONDS_PER_DAY * MAX_DELAY):
                        assign_geotag_from_file(file, gps_file)
                        return True
                    else:
                        logging.warn("Closest file (%s : %s) out of delay %f (max_delay = %f). File to tag (%s : %s)",
                                     gps_file,
                                     date_gps.strftime(FORMAT), delay, MAX_DELAY * SECONDS_PER_DAY, file, date_file.strftime(FORMAT))
                else:
                    logging.warn("No date in file %s", file)
            else:
                logging.warn("No date in file %s", gps_file)
        else:
            logging.warn("No GPS files found for %s. No date in EXIF?", file)
    else:
        logging.warn("file to tag is None")
    global NB_NOT_TAGGED_FILE
    NB_NOT_TAGGED_FILE = NB_NOT_TAGGED_FILE + 1
    return False

def log_stats():
    logging.info("------- GPS TAG RESULTS ------- ")
    logging.info("%i files TAGGED", NB_TAGGED_FILE)
    logging.info("%i files ALREADY TAGGED", NB_ALREADY_TAGGED_FILE)
    logging.info("%i files NOT TAGGED", NB_NOT_TAGGED_FILE)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', type=dir_path, required=True, help='path to the folder with photos to tag')
    parser.add_argument('--gps', type=dir_path, nargs="+", required=True,
                        help='path to the folder containing photo with GPS data')
    parser.add_argument('--delay', type=float,
                        help='max delay in days between GPS photo and photo to tag')
    parsed_args = parser.parse_args()
    if parsed_args.delay:
        global MAX_DELAY
        MAX_DELAY = parsed_args.delay
    logging.info('STEP 1 ---> Loading tagged photos')
    #for folder in parsed_args.gps:
        #logging.info('       %i/%i = Loading folder %s', parsed_args.gps.index(folder) + 1, len(parsed_args.gps), folder)
    load_tagged_folder(parsed_args.gps)

    logging.info('STEP 2 ---> Tag photos')
    os.chdir(parsed_args.tag)
    for file in tqdm(glob.glob("*.JP*G") + glob.glob("*.jp*g")):
        tag_photo(file)
    log_stats()

if __name__ == "__main__":
    main()