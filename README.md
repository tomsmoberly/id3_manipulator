# ID3 Manipulator

ID3 Manipulator is used to copy unsorted mp3 files into a directory where the files are neatly sorted according to their ID3 tags. It takes a source directory and destination directory as inputs and moves all mp3s found in the source directory tree to destination_directory/artist/album/title.mp3, making some substitutions to make the path friendly (e.g. it would replace a forward slash character).

#### Usage:

python3 id3_manipulator.py [command] [source_directory] [destination_directory]

#### Example:

python3 id3_manipulator.py copy_sort /home/tom/unsorted_music /home/tom/sorted_music
