"""
    Procedure for sorting files in directory
    All files and folders are renamed using the normalize function;
    File extensions do not change after renaming;
    Empty folders are deleted;
    The unpacked contents of the archive are transferred to the archives' folder
    in a sub folder named the same as the archive;
    Files whose extensions are unknown remain unchanged.
    Added Asyncio operations for moving files
"""

import os
import re
import shutil
import sys
import asyncio

from aiopath import AsyncPath
from aioshutil import move


CYRILLIC_SYMBOLS = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ'
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "u", "ja", "je", "ji", "g")

TRANS = {}
for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS[ord(c)] = l
    TRANS[ord(c.upper())] = l.upper()


def normalize(name: str) -> str:
    t_name = name.translate(TRANS)
    t_name = re.sub(r'[^a-zA-Z\d_\.]', '_', t_name)
    return t_name


# key names is new folder names
extensions = {

    'images': ['jpeg', 'png', 'jpg', 'svg'],

    'video': ['avi', 'mp4', 'mov', 'mkv'],

    'documents': ['pdf', 'txt', 'doc', 'docx', 'rtf', 'tex', 'wpd', 'odt', 'xls', 'xlsx'],

    'audio': ['mp3', 'ogg', 'wav', 'amr'],

    'archives': ['zip', 'gz', 'tar'],

    'other': []
}

inv_dict_ext = {}
for key, value in extensions.items():
    for val in value:
        inv_dict_ext[f'.{val}'] = key

if len(sys.argv) != 2:
    print("\n\033[31mNeed a name of the folder for sorting\033[0m\n")
    quit()
else:
    root_folder = AsyncPath(sys.argv[1])


def create_folders_from_list(folder_path, folder_names) -> None:
    for folder in folder_names:
        os.mkdir(folder_path / folder)


async def tree_items(path: AsyncPath) -> None:
    async for el in path.iterdir():
        if await el.is_dir():
            await tree_items(el)
        else:
            await move_file(el)


async def move_file(file: AsyncPath) -> None:
    ext = file.suffix
    new_path = root_folder / inv_dict_ext.get(ext, "other")
    try:
        await move(file, new_path)
    except OSError as err:
        print(err)


def remove_empty_folders(folder_path):
    dir_list = []
    for root, dirs, files in os.walk(folder_path):
        dir_list.append(root)
    for root in dir_list[::-1]:
        if not os.listdir(root):
            os.rmdir(root)


def unpack_file(folder_path):
    for archive in os.listdir(folder_path):
        archive_name = archive.split('.')[0]
        if not os.path.exists(folder_path / archive_name):
            os.mkdir(folder_path / archive_name)
        shutil.unpack_archive(folder_path / archive, folder_path / archive_name)
        os.remove(folder_path / archive)


def main():
    create_folders_from_list(root_folder, extensions)

    base_folder = AsyncPath(root_folder)
    asyncio.run(tree_items(base_folder))

    remove_empty_folders(root_folder)
    unpack_file(root_folder / 'archives')


if __name__ == "__main__":
    main()
