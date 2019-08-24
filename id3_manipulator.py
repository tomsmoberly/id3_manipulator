"""
Copies all mp3s found in source folder tree to sorted folders in the destination folder based on ID3 tags.

This script scans all mp3s in the source folder and any sub-folders and moves them to
destination_folder/artist/album/title.mp3, where artist, album and title are the ID3 tags. If any of those
ID3 tags are missing, the file is not copied and a time/date-stamped text file is output in the script's
root folder containing the paths of files that were not copied.

Script takes 3 inputs, the command, the source folder, and the destination folder. As of now,
the only valid command is "copy_sort", but it's a required input in case additional features are added.

Example:
    python3 id3_manipulator.py copy_sort /home/tom/unsorted_music /home/tom/sorted_music
"""

# Copyright (C) 2019 Thomas Moberly
# License can be found in LICENSE.txt file
# 3rd party licenses can be found in the LICENSE_3RD_PARTY.txt file

import shutil
import datetime
import os
import filecmp
import sys
from mutagen.id3 import ID3

def make_friendly_path(path):
    """ 
    Replaces some characters that don't work well in filenames/directories

    This function replaces all characters that would be unsupported on modern windows or
    unix-based systems. It also replaces some that would be annoying when working in a terminal
    (such as spaces). However, it leaves in parentheses and square brackets because they're
    pretty common in mp3 tags and there's no great substitute. It also replaces invalid chars
    with a period, which may not be to everyone's taste.
    """
    path = path.lower()
    path = path.replace(' ', '_')
    path = path.replace('/', '_')
    # Replace all characters that are not alphanumeric or .-_()[] with a . for friendlier paths.
    # This character set is a personal choice.
    path = "".join([ c if (c.isalnum() or c == '-' or c == '_' or c == '.' or c == '(' or c == ')' or c == '[' or c == ']') else "." for c in path ])
    return path

def move_mp3(src_path, dest_path_root):
    """
    Moves the input mp3 to dest_path_root/artist/album/title.mp3 based on ID3 tags
    
    This checks for an existing file at the above path. If one already exists, the contents
    are compared. If they are identical, the file is not copied. If they are different, the
    file is copied as title_1.mp3. If title_1.mp3 exists and it is not identical to the input,
    the file is copied as title_2.mp3, etc.

    Arguments:
    src_path -- location of mp3 to be moved
    dest_path_root -- the root folder of sorted mp3s containing artist folders

    Returns:
    1 on successful copy or identical file in place, 0 on failure
    """
    audio = ID3(src_path)
    #year = str(audio['TDRC'])
    if 'TPE1' in audio:
        artist = make_friendly_path(str(audio['TPE1']))
    else:
        return 0
    if 'TALB' in audio:
        album = make_friendly_path(str(audio['TALB']))
    else:
        return 0
    if 'TIT2' in audio:
        title = make_friendly_path(str(audio['TIT2']))
    else:
        return 0
    
    artist_path = os.path.join(dest_path_root, artist)
    try:
        # Make artist dir if it does not exist
        os.makedirs(artist_path)
    except FileExistsError:
        pass
    album_path = os.path.join(artist_path, album)
    try:
        # Make album dir if it does not exist
        os.makedirs(album_path)
    except FileExistsError:
        pass
    
    dest_base = os.path.join(album_path, title)
    # modified_dest_base used to account for titles like title_1 when duplicate titles are found.
    modified_dest_base = dest_base
    duplicate_count = 0
    # If file exists, check if files are same with filecmp. If not, make one with appended _1 or _2 or...
    # If they are same, do not copy. If the file does not exist, copy. 
    while os.path.exists(modified_dest_base + '.mp3'):
        if filecmp.cmp(src_path, modified_dest_base + '.mp3'):
            # Files are the same, no need to copy but file is considered successfully sorted
            return 1
        duplicate_count += 1
        modified_dest_base = dest_base + '_' + str(duplicate_count)
    print('Sorting', src_path)
    shutil.copy2(src_path, modified_dest_base + '.mp3')
    return 1

def organize_by_id3(src_path, dest_path):
    """Traverses src_path tree and sorts all .mp3 files under dest_path."""
    move_failures = list()
    for root, dirs, files in os.walk(src_path):
        for name in files:
            filename, file_extension = os.path.splitext(name)
            if  file_extension.lower() == '.mp3':
                src_path = os.path.join(root, name)
                successful_move = move_mp3(src_path, dest_path)
                if not successful_move:
                    move_failures.append(src_path)
    
    if len(move_failures) < 1:
        return 1
    # Print and make file tracking failures
    script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    now = datetime.datetime.now()
    failure_filename = "failures" + str(now.year) + '-' + str(now.month) + '-' + str(now.day) + '_' + str(now.hour) + '-' + str(now.minute) + '-' + str(now.second) + '.txt'
    failure_filename = os.path.join(script_path,failure_filename)
    failure_file = open(failure_filename, 'w')
    print('\nThe following files failed due to missing ID3 tags:')
    for fail in move_failures:
        print(fail)
        failure_file.write(fail + '\n')
    failure_file.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("id3_organizer.py requires 3 input arguments:")
        print("command, source_folder, destination_folder")
        print("Example:\npython3 id3_manipulator.py copy_sort home/tom/unsorted_music home/tom/sorted_music")
    else:
        if sys.argv[1] == 'copy_sort':
            source_folder = sys.argv[2]
            destination_folder = sys.argv[3]
            if not os.path.isdir(source_folder):
                print("Source folder (argument 2) is not a valid directory.")
            else:
                if not os.path.isdir(destination_folder):
                    print("Destination folder (argument 3) is not a valid directory.")
                else:
                    organize_by_id3(source_folder, destination_folder)
        else:
            print(sys.argv[1], "(argument 1) is not a supported command.")
