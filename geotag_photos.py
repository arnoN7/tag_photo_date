import glob, os, sys, time
import pandas as pd
import piexif
from datetime import datetime
from tqdm import tqdm


DIR_TO_TAG = "/Users/administrateur/Pictures/testgeotag/totag"
DIR_TAGGED = "/Users/administrateur/Pictures/testgeotag/tagged"
closest_tag_file =""
FORMAT='%Y-%m-%d %H:%M:%S'
EXIF_FORMAT='%Y:%m:%d %H:%M:%S'

def nearest_tagged_file(directory, non_tagged_file):
    d = []
    os.chdir(directory)
    for file in tqdm(glob.glob("*.JP*G")):
        d.append(
            {
                'FILE': file,
                'DATE': get_file_date(file, True)
            }
        )
    df = pd.DataFrame(d)
    df.DATE = pd.to_datetime(df.DATE, format=FORMAT)
    dt = pd.to_datetime(get_file_date(non_tagged_file, False), format=FORMAT)
    #print(pd.to_datetime(df['DATE']))
    print(non_tagged_file)
    print(get_file_date(non_tagged_file, False))
    return (df.loc[(pd.to_datetime(df['DATE'])
                      - dt).abs().idxmin(),'FILE'])


def get_file_date(file, checkGPS):
    exif_dict = piexif.load(file)
    if piexif.ImageIFD.DateTime not in exif_dict['0th']:
        print('No Date for ' + file)
        return None
    else:
        try:
            date_b = exif_dict['0th'][piexif.ImageIFD.DateTime]
            if checkGPS:
                if (1 not in exif_dict['GPS']):
                    #print('No GPS found for ' + file)
                    #print(exif_dict['GPS'])
                    return None
            return datetime.strptime(date_b.decode("utf-8"), '%Y:%m:%d %H:%M:%S').strftime(FORMAT)
        except ValueError:
            print('Invalid date format in EXIF found for ' + file + ' date found : '+ date_b.decode("utf-8"))
            return None


def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))

def assign_geotag_from_file(file, tagged_file):
    tagged_file = os.path.join(DIR_TAGGED, tagged_file)
    print("Tagged " + tagged_file)
    print("To Tag " + file)
    os.chdir(DIR_TO_TAG)
    exif_dict_tagged = piexif.load(tagged_file)
    print(exif_dict_tagged['GPS'])
    exif_dict = piexif.load(file)
    exif_dict['GPS'] = exif_dict_tagged['GPS']
    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, file)
    print(file + " Tagged")
    return True

def tag_photo(file):
    tagged_file = nearest_tagged_file(DIR_TAGGED, file)
    assign_geotag_from_file(file, tagged_file)
    return True

def main():
    file = DIR_TO_TAG + "/P4190217.JPG"
    print(file)
    tag_photo(file)

if __name__ == "__main__":
    main()