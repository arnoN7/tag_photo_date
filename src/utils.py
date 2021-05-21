import os

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        print(string + "Not a directory")
        exit(1)