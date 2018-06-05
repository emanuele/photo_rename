from glob import glob
from shutil import move

if __name__ == '__main__':
    suffix = '.ARW'
    dir_in = 'dump/'
    dir_out = 'raw/'
    event_name = 'YYYYMMDD_location-short-event-description'
    offset_number = 0  # if you want filenames to start from 1+offset_number...
    filename_out = dir_out + event_name + '_%04d' + suffix
    filenames_in = sorted(glob(dir_in + '*' + suffix))  # sorted() is absolutely necessary!!
    for i, fn_in in enumerate(filenames_in):
        fn_out = filename_out % (i + 1 + offset_number)
        print("moving %s to %s" % (fn_in, fn_out))
        # move(fn_in, fn_out)
