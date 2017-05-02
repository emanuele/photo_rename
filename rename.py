from glob import glob
import exifread
from os.path import getmtime, getctime, basename, exists
from os import makedirs
import time
import numpy as np
from shutil import copy2, move
from joint_argsort import joint_argsort
from itertools import chain


class PictureFile(object):
    def __init__(self, filename_absolute):
        self.filename_absolute = filename_absolute
        self.filename_relative = basename(self.filename_absolute)
        self.extension = filename_absolute[-4:]
        self.get_filename_sequence_number()

    def get_filename_sequence_number(self):
        assert((self.filename_relative[:4] == 'SAM_') or
               (self.filename_relative[:4] == 'DSC0'))  # check Samsung filename format
        self.filename_sequence_number = self.filename_relative[4:8]  # valid for Samsung and Sony only!
        try:
            self.filename_sequence_number = int(self.filename_sequence_number)
        except ValueError:
            print("Cannot parse filename_sequence_number from %s" % self.filename_sequence_number)
            raise Exception

    def get_file_ctime(self):
        self.file_ctime = getctime(self.filename_absolute)

    def get_file_exif_infos(self):
        self.tags = exifread.process_file(open(self.filename_absolute))
        self.file_exif_datetime_original = self.tags['EXIF DateTimeOriginal'].values
        self.file_exif_datetime_original = time.mktime(time.strptime(self.file_exif_datetime_original, "%Y:%m:%d %H:%M:%S"))
        self.file_exif_datetime_image = self.tags['Image DateTime'].values
        self.file_exif_datetime_image = time.mktime(time.strptime(self.file_exif_datetime_image, "%Y:%m:%d %H:%M:%S"))
        assert(self.file_exif_datetime_original == self.file_exif_datetime_image)

class PictureCollection(object):
    def __init__(self, name, pfs=None, date=None):
        self.name = name
        self.pfs = pfs
        self.date = date  # string %Y%m%d
        self.consistent = False

    def check_consistency(self, exclude_ctimes=False):
        exif_ctimes = [pf.file_exif_datetime_image for pf in self.pfs]
        file_ctimes = [pf.file_ctime for pf in self.pfs]
        sequence_numbers = [pf.filename_sequence_number for pf in self.pfs]
        exif_ctimes_order = joint_argsort(exif_ctimes, sequence_numbers)
        file_ctimes_order = joint_argsort(file_ctimes, sequence_numbers)
        sequence_numbers_order = np.argsort(sequence_numbers)
        self.order = None
        self.match_exif_file = True
        if (exif_ctimes_order != file_ctimes_order).any():
            print("WARNING! exif_ctimes order do not match file_ctimes order.")
            print("exif_ctimes_order: %s" % exif_ctimes_order)
            print("file_ctimes_order: %s" % file_ctimes_order)
            self.match_exif_file = False

        self.match_exif_sequence = True
        if (exif_ctimes_order != sequence_numbers_order).any():
            print("WARNING! exif_ctimes order do not match sequence_numbers order.")
            print("exif_ctimes_order: %s" % exif_ctimes_order)
            print("sequence_numbers_order: %s" % sequence_numbers_order)
            self.match_exif_sequence = False

        self.match_file_sequence = True
        if (file_ctimes_order != sequence_numbers_order).any():
            print("WARNING! file_ctimes order do not match sequence_numbers order.")
            print("file_ctimes_order: %s" % file_ctimes_order)
            print("sequence_numbers_order: %s" % sequence_numbers_order)
            self.match_file_sequence = False

        if (self.match_exif_file == True and self.match_exif_sequence == True and self.match_file_sequence == True) or (exclude_ctimes and self.match_exif_sequence == True):
            self.consistent = True
            self.argsort = sequence_numbers_order
            self.order = np.argsort(self.argsort)
            if not exclude_ctimes:
                print("EXIFs, file metadata and sequence numbers are consistent!")
            else:
                print("EXIFs and sequence numbers are consistent!")


    def compute_new_names(self, initial_number=1, digits=4):
        self.initial_number = initial_number
        self.digits = digits
        if self.date == None:
            initial_ctime = time.localtime(self.pfs[np.where(pc.order == 0)[0][0]].file_exif_datetime_image)
            self.date = time.strftime("%Y%m%d", initial_ctime)

        self.format = "%0" + str(digits) + 'd'
        self.template = self.date + '_' + self.name + '_' + self.format + '%s'
        self.new_names = [self.template % (oi + self.initial_number, self.pfs[oi].extension) for oi in self.order]
        self.old_names = [pf.filename_relative for pf in self.pfs]

    def rename(self, target_folder_name, initial_number=1, digits=4, copy=True):
        if self.consistent == False:
            print("ERROR! There is no consistency, please fix that first")
            return

        self.target_folder_name = target_folder_name
        if not exists(target_folder_name):
            print("Creating %s" % target_folder_name)
            makedirs(target_folder_name)

        self.compute_new_names(initial_number=initial_number, digits=digits)
        for i, pf in enumerate(self.pfs):
            source = pf.filename_absolute
            destination = target_folder_name + self.new_names[i]
            if copy:
                print("%d) Copying %s to %s" %(i, source, destination))
                copy2(source, destination)  # copy2 keeps original timestamp
            else:
                print("%d) Moving %s to %s" % (i, source, destination))
                move(source, destination)


if __name__ == '__main__':
    # event_name = 'trento-compleanno-nausicaa'
    origin_sequence_min = 0000
    origin_sequence_max = 9999
    origin_folder_name = '/mnt/DCIM/268PHOTO/'
    target_folder_name = '/tmp/raw/'

    glob_patterns = ['*.SRW', '*.JPG']

    origin_filename_format = 'SAM_%04d.JPG'
    assert((origin_sequence_min >= 0) and (origin_sequence_min <= 9999))
    assert((origin_sequence_max >= 0) and (origin_sequence_max <= 9999))
    assert(origin_sequence_min <= origin_sequence_max)
    filename_relative = origin_filename_format % origin_sequence_min
    filename_absolute = origin_folder_name + filename_relative
    filenames_in_folder = sorted(chain.from_iterable(glob(origin_folder_name + gb) for gb in glob_patterns))

    pfs = []
    print("Getting infos from all files between min (%s) and max (%s):")
    print("%s files present." % len(filenames_in_folder))
    for i, fn in enumerate(filenames_in_folder):
        print(fn)
        pf = PictureFile(fn)
        if (pf.filename_sequence_number >= origin_sequence_min) and (pf.filename_sequence_number <= origin_sequence_max):
            pf.get_file_ctime()
            print("%d) %s ctime: %s" % (i, pf.filename_relative, pf.file_ctime))
            pf.get_file_exif_infos()
            print("%s exif_datetime_image: %s" % (pf.filename_relative, pf.file_exif_datetime_image))
            pfs.append(pf)
        else:
            print("SKIPPED")

    pc = PictureCollection(event_name, pfs)
    pc.check_consistency()
    # pc.rename(target_folder_name)
