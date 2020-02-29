import flirpy.io.seq
import glob
import natsort
from tqdm import tqdm
import argparse
import os
import shutil
import logging

def add_bool_arg(parser, name, help_string="", default=False):
    # https://stackoverflow.com/a/31347222
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--' + name, dest=name, help=help_string, action='store_true')
    group.add_argument('--no_' + name, dest=name, help=help_string, action='store_false')
    parser.set_defaults(**{name:default})

def recursive_copy(src, dst):

    items = os.listdir(src)

    for item in items:

        item_path = os.path.join(src, item)
        new_dst = os.path.abspath(os.path.join(dst, item))

        if os.path.isfile(item_path):
            shutil.copy(item_path, new_dst)

        elif os.path.isdir(item_path):
            os.makedirs(new_dst, exist_ok=True)
            recursive_copy(item_path, new_dst)
    
    return


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Split all files in folder')
    parser.add_argument('-o', '--output', help='Output folder', default="./")
    parser.add_argument('-i', '--input', help='Input file mask', required=True)
    parser.add_argument('-v', '--verbosity', help='Logging level', default='info')
    parser.add_argument('--preview_format', help='Output preview format (png, jpg, tiff)', default='jpg')

    add_bool_arg(parser, name='merge_folders', help_string='Merge output folders (and remove intermediates afterwards)', default=True)
    add_bool_arg(parser, name='split_filetypes', help_string='Split output files by type (make raw/preview/radiometric folders)', default=True)
    add_bool_arg(parser, name='export_meta', help_string='Export meta information files (also for geotagging)', default=True)
    add_bool_arg(parser, name='export_tiff', help_string='Export radiometric tiff files', default=True)
    add_bool_arg(parser, name='export_preview', help_string='Export 8-bit preview png files', default=True)

    args = parser.parse_args()

    if args.verbosity is not 'quiet':
        numeric_level = getattr(logging, args.verbosity.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % args.verbosity)
        logging.basicConfig(level=numeric_level)
    
    output_folder = os.path.abspath(args.output)
    input_mask = args.input

    if output_folder is not "./":
        os.makedirs(output_folder, exist_ok=True)

    files = natsort.natsorted(glob.glob(input_mask))
    
    print("Input files: ", files)
 
    splitter = flirpy.io.seq.splitter(output_folder, preview_format=args.preview_format)
    splitter.split_filetypes = args.split_filetypes
    splitter.export_meta = args.export_meta
    splitter.export_tiff = args.export_tiff
    splitter.export_preview = args.export_preview

    folders = splitter.process(files)

    if args.merge_folders:
        print("Merging folders")
        gpslog = open(os.path.join(output_folder, "flightlog.txt"), 'w')
        gpslog.write('ignore1,ignore2,Latitude,Longitude,Heading,ignore3,ignore4,ignore5,ignore6\n')

        for folder in tqdm(folders):
            print("Copying: {}".format(folder))
            gpslog_local = open(os.path.join(folder, "gpsLog.txt"), 'r')
            with open(os.path.join(folder, "gpsLog.txt"), 'r') as gpslog_local:
                for line in gpslog_local:
                    gpslog.write(line)

            recursive_copy(folder, output_folder)
            shutil.rmtree(folder)

        gpslog.close()
