"""
Copies audio in source tree to sorted folders in the dest folder based on tags

This script scans all audio files in the source folder and any sub-folders and 
moves them to destination_folder/artist/album/title.mp3, where artist, album and 
title are the tags. If any of those tags are missing, the file is not
copied and a text file is output in the script's root folder
containing the paths of files that were not copied.

Script takes 3 inputs, the command, the source folder, and the destination
folder. As of now, the only valid command is "copy_sort", but it's a required
input in case additional features are added.

Example:
    python3 id3_manipulator.py copy_sort /home/tom/unsorted /home/tom/sorted
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
from mutagen.flac import FLAC

def make_friendly_path(path):
    """ 
    Replaces characters that don't work in filenames/directories

    This function replaces all characters that would be unsupported
    on modern windows or unix-based systems. 
    """
    #path = path.lower()
    #path = path.replace(' ', '_')
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    # Replace all invalid characters so the file can be saved.
    path = "".join([ c if (c not in invalid_chars) else "_" for c in path ])
    return path

def move_audio_file(src_path, dest_path_root):
    """
    Moves the input to dest_path_root/artist/album/title.[ext] based on tags
    
    This checks for an existing file at the above path. If one already exists, 
    the contents are compared. If they are identical, the file is not copied.
    If they are different, the file is copied as title_1.[ext]. If title_1.[ext]
    exists and it is not identical to the input, the file is copied as 
    title_2.[ext], etc.

    Arguments:
    src_path -- location of file to be moved
    dest_path_root -- the root folder of sorted files containing artist folders

    Returns:
    1 on successful copy or identical file in place, 0 on failure
    """
    filename, file_extension = os.path.splitext(src_path)
    if file_extension.lower() == '.flac':
        try:
            audio = FLAC(src_path)
        except:
            return 0
        if 'artist' in audio:
            if len(audio['artist']) == 1:
                artist = make_friendly_path(audio['artist'][0])
            else:
                return 0
        else:
            return 0
        if 'album' in audio:
            if len(audio['album']) == 1:
                album = make_friendly_path(audio['album'][0])
            else:
                return 0
        else:
            return 0
        if 'title' in audio:
            if len(audio['title']) == 1:
                title = make_friendly_path(audio['title'][0])
            else:
                return 0
        else:
            return 0
    else:
        try:
            audio = ID3(src_path)
        except:
            return 0
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
        # print(artist + "-" + album + '-' + title)
    
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
    # modified_dest_base used to account for titles like title_1 
    # when duplicates titles are found.
    modified_dest_base = dest_base
    duplicate_count = 0
    # If file exists, check if files are same with filecmp. If not, make one 
    # with appended _1 or _2 or...
    # If they are same, do not copy. If the file does not exist, copy. 
    while os.path.exists(modified_dest_base + file_extension):
        if filecmp.cmp(src_path, modified_dest_base + file_extension):
            # Files are the same, no need to copy but file is considered successfully sorted
            return 1
        duplicate_count += 1
        modified_dest_base = dest_base + '_' + str(duplicate_count)
    print('Sorting', src_path)
    shutil.copy2(src_path, modified_dest_base + file_extension)
    return 1

def organize_by_tag(src_path, dest_path):
    """Traverses src_path tree and sorts all audio files under dest_path."""
    valid_exts = ['.flac', '.mp3']
    unsupported_exts = ['.wav', '.pcm', '.aiff', '.aac', '.m4a', '.ogg', '.wma',
                       '.aac', '.alac', '.ape', '.opus', '.ra', '.rm', '.vox']
    move_failures = list()
    unsupported_files = list()
    for root, dirs, files in os.walk(src_path):
        # root here is the folder that files are in
        # use it to get tag fail info and move failed folders.
        for name in files:
            filename, file_extension = os.path.splitext(name)
            ext = file_extension.lower()
            if ext in valid_exts:
                file_src_path = os.path.join(root, name)
                successful_move = move_audio_file(file_src_path, dest_path)
                if not successful_move:
                    move_failures.append(file_src_path)
            elif ext in unsupported_exts:
                file_src_path = os.path.join(root, name)
                unsupported_files.append(file_src_path)

    
    if len(move_failures) < 1 and len(unsupported_files) < 1:
        return 1
    # Print and make file tracking failures
    script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    now = datetime.datetime.now()
    path_for_file = os.path.basename(os.path.normpath(src_path))
    path_for_file = '_' + path_for_file.replace(' ', '_')
    path_for_file = make_friendly_path(path_for_file) + '.txt'
    output_dir = os.path.join(script_path,'output')
    if not os.path.exists(output_dir):
        os.makedirs('output')
    if len(move_failures) >= 1:
        failure_filename = "failures" + path_for_file
        # str(now.year) + '-' + str(now.month) + '-' + str(now.day) + '_' 
        # + str(now.hour) + '-' + str(now.minute) + '-' + str(now.second) + '.txt'
        failure_filename = os.path.join(script_path, output_dir, failure_filename)
        failure_file = open(failure_filename, 'w')

        print('\nThe following files failed, likely due to missing tags:')
        for fail in move_failures:
            print(fail)
            failure_file.write(fail + '\n')
        failure_file.close()
    if len(unsupported_files) >= 1:
        unsupported_filename = "unsupported" + path_for_file
        # str(now.year) + '-' + str(now.month) + '-' + str(now.day) + '_' 
        # + str(now.hour) + '-' + str(now.minute) + '-' + str(now.second) + '.txt'
        unsupported_filename = os.path.join(script_path, output_dir, unsupported_filename)
        unsupported_file = open(unsupported_filename, 'w')

        print('\nThe following files are not yet supported:')
        for fail in unsupported_files:
            print(fail)
            unsupported_file.write(fail + '\n')
        unsupported_file.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("id3_organizer.py requires 3 input arguments:")
        print("command, source_folder, destination_folder")
        print("Example:\npython3 id3_manipulator.py copy_sort "
              "home/tom/unsorted_music home/tom/sorted_music")
    else:
        if sys.argv[1] == 'copy_sort':
            source_folder = sys.argv[2]
            destination_folder = sys.argv[3]
            if not os.path.isdir(source_folder):
                print("Source folder (argument 2) is not a valid directory.")
            else:
                if not os.path.isdir(destination_folder):
                    print("Destination folder (argument 3) "
                          "is not a valid directory.")
                else:
                    organize_by_tag(source_folder, destination_folder)
        else:
            print(sys.argv[1], "(argument 1) is not a supported command.")
