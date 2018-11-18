"""
Use imagemagick to convert all pfds to a sequence of thumbnail images
"""

import argparse
import os
import time
import shutil
from subprocess import Popen


parser = argparse.ArgumentParser(description="Gridify thumbnails from pdf file")
parser.add_argument('--pdf', type=str, help="path to pdf file")
parser.add_argument('--npages', type=int, default=8, help="number of pages to thumbify")
# Default is set to 8 since 9th page are (usually) references
parser.add_argument('--ncols', type=int, default=5)
parser.add_argument('--dpi', type=int, default=150, help="resolution expressed in Dots Per Inch")
args = parser.parse_args()


def gridify(args):

    # Define zero padding width
    padding = 3
    # Define configutation suffix
    suffix = "_npages{}_ncols{}_dpi{}".format(args.npages, args.ncols, args.dpi)

    # Make sure imagemagick is installed
    if not shutil.which('convert'):  # shutil.which needs Python 3.3+
        raise RuntimeError("imagemagick must be installed")
    # Make sure the given file has the right extension
    assert args.pdf.endswith('.pdf'), "extension must be pdf"
    # Create thumbnail file name
    thumb_grid_img = args.pdf.replace('.pdf', "{}.jpg".format(suffix))
    # Create directory that will contain the preprocessing files
    preproc_dir = "{}.preproc".format(args.pdf.replace('.pdf', suffix))
    if not os.path.exists(preproc_dir):
        os.makedirs(preproc_dir)
    else:
        # Quit if the preprocessing files from a previous gridification
        # of the same pdf at the same location are still present
        print(("quitting, preprocessing files already exist for {} "
               "in the directory {}".format(args.pdf, os.path.join(os.getcwd(), preproc_dir))))
        raise SystemExit
    # Quit if the thumbnail grid file already exists
    if os.path.isfile(thumb_grid_img):
        print(("quitting, thumbnail grid already exists for {} "
               "in the directory {}".format(args.pdf, os.getcwd())))
        raise SystemExit

    # Spawn asynchronous workers to generate X independent images of the thumbnails:
    #   thumb-0.png ... thumb-(X-1).png
    pp = Popen(['convert',
                '-density', '{}'.format(args.dpi),
                '{}[0-{}]'.format(args.pdf, args.npages - 1),
                '-quality', '100',
                '-shave', '24',
                os.path.join(preproc_dir, "thumb-%0{}d.png".format(padding))])

    # Since convert can unfortunately enter an infinite loop, we have to handle this manually
    start_time = time.time()
    while time.time() - start_time < 60:  # give it 60 seconds deadline
        ret = pp.poll()  # check if child process has terminated
        if ret is not None:  # None value indicates that the process hasn’t terminated yet
            # Process has terminated
            break
        time.sleep(0.1)
    ret = pp.poll()  # check if child process has terminated
    if ret is None:
        print("convert command did not terminate in 60 seconds, terminating.")
        pp.terminate()  # give up

    if os.path.isfile(os.path.join(preproc_dir, "thumb-{}.png".format('0' * padding))):
        cmd_fmt = "montage -mode concatenate -quality 100 -tile {} {} {}"
        cmd = cmd_fmt.format(args.ncols,
                             os.path.join(preproc_dir, "thumb-*.png"),
                             thumb_grid_img)
        print(cmd)
        os.system(cmd)
    else:
        raise RuntimeError("missing initial thumnail image, assembly aborted")

    time.sleep(0.01)  # silly way for allowing for ctrl+c termination


if __name__ == "__main__":
    # Gridify thumbnails from pdf files
    gridify(args)
