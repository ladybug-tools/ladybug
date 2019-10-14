# coding=utf-8
"""Utility functions for working with files and directories."""
from __future__ import division

import os
import shutil
import zipfile
import sys

if (sys.version_info < (3, 0)):
    import urllib2
    readmode = 'rb'
    writemode = 'wb'
else:
    import urllib.request
    readmode = 'r'
    writemode = 'w'


def preparedir(target_dir, remove_content=True):
    """Prepare a folder for analysis.

    This method creates the folder if it is not created, and removes the file in
    the folder if the folder already existed.
    """
    if os.path.isdir(target_dir):
        if remove_content:
            nukedir(target_dir, False)
        return True
    else:
        try:
            os.makedirs(target_dir)
            return True
        except Exception as e:
            print("Failed to create folder: %s\n%s" % (target_dir, e))
            return False


def nukedir(target_dir, rmdir=False):
    """Delete all the files inside target_dir.

    Usage:

    .. code-block:: python

        nukedir("c:/ladybug/libs", True)
    """
    d = os.path.normpath(target_dir)

    if not os.path.isdir(d):
        return

    files = os.listdir(d)

    for f in files:
        if f == '.' or f == '..':
            continue
        path = os.path.join(d, f)

        if os.path.isdir(path):
            nukedir(path)
        else:
            try:
                os.remove(path)
            except Exception:
                print("Failed to remove %s" % path)

    if rmdir:
        try:
            os.rmdir(d)
        except Exception:
            print("Failed to remove %s" % d)


def write_to_file_by_name(folder, fname, data, mkdir=False):
    """Write a string of data to file by filename and folder.

    Args:
        folder: Target folder (e.g. c:/ladybug).
        fname: File name (e.g. testPts.pts).
        data: Any data as string.
        mkdir: Set to True to create the directory if doesn't exist (Default: False).
    """
    if not os.path.isdir(folder):
        if mkdir:
            preparedir(folder)
        else:
            created = preparedir(folder, False)
            if not created:
                raise ValueError("Failed to find %s." % folder)

    file_path = os.path.join(folder, fname)

    with open(file_path, writemode) as outf:
        try:
            outf.write(str(data))
            return file_path
        except Exception as e:
            raise IOError("Failed to write %s to file:\n\t%s" % (fname, str(e)))


def write_to_file(file_path, data, mkdir=False):
    """Write a string of data to file.

    Args:
        file_path: Full path for a valid file path (e.g. c:/ladybug/testPts.pts)
        data: Any data as string
        mkdir: Set to True to create the directory if doesn't exist (Default: False)
    """
    folder, fname = os.path.split(file_path)
    return write_to_file_by_name(folder, fname, data, mkdir)


def copy_files_to_folder(files, target_folder, overwrite=True):
    """Copy a list of files to a new target folder.

    Returns:
        A list of fullpath of the new files.
    """
    if not files:
        return []

    for f in files:
        target = os.path.join(target_folder, os.path.split(f)[-1])

        if target == f:
            # both file path are the same!
            return target

        if os.path.exists(target):
            if overwrite:
                # remove the file before copying
                try:
                    os.remove(target)
                except Exception:
                    raise IOError("Failed to remove %s" % f)
                else:
                    shutil.copy(f, target)
            else:
                continue
        else:
            print('Copying %s to %s' % (os.path.split(f)[-1],
                                        os.path.normpath(target_folder)))
            shutil.copy(f, target)

    return [os.path.join(target_folder, os.path.split(f)[-1]) for f in files]


def bat_to_sh(file_path):
    """Convert honeybee .bat file to .sh file.

    WARNING: This is a very simple function and doesn't handle any edge cases.
    """
    sh_file = file_path[:-4] + '.sh'
    with open(file_path, 'rb') as inf, open(sh_file, 'wb') as outf:
        outf.write('#!/usr/bin/env bash\n\n')
        for line in inf:
            # pass the path lines, etc to get to the commands
            if line.strip():
                continue
            else:
                break

        for line in inf:
            if line.startswith('echo'):
                continue
            modified_line = line.replace('c:\\radiance\\bin\\', '').replace('\\', '/')
            outf.write(modified_line)

    print('bash file is created at:\n\t%s' % sh_file)
    # Heroku - Make command.sh executable
    st = os.stat(sh_file)
    os.chmod(sh_file, st.st_mode | 0o111)
    return sh_file


def _download_py2(link, path, __hdr__):
    """Download a file from a link in Python 2."""
    try:
        req = urllib2.Request(link, headers=__hdr__)
        u = urllib2.urlopen(req)
    except Exception as e:
        raise Exception(' Download failed with the error:\n{}'.format(e))

    with open(path, 'wb') as outf:
        for l in u:
            outf.write(l)
    u.close()


def _download_py3(link, path, __hdr__):
    """Download a file from a link in Python 3."""
    try:
        req = urllib.request.Request(link, headers=__hdr__)
        u = urllib.request.urlopen(req)
    except Exception as e:
        raise Exception(' Download failed with the error:\n{}'.format(e))

    with open(path, 'wb') as outf:
        for l in u:
            outf.write(l)
    u.close()


def download_file_by_name(url, target_folder, file_name, mkdir=False):
    """Download a file to a directory.

    Args:
        url: A string to a valid URL.
        target_folder: Target folder for download (e.g. c:/ladybug)
        file_name: File name (e.g. testPts.zip).
        mkdir: Set to True to create the directory if doesn't exist (Default: False)
    """
    # headers to "spoof" the download as coming from a browser (needed for E+ site)
    __hdr__ = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 '
               '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
               'Accept': 'text/html,application/xhtml+xml,'
               'application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}

    # create the target directory.
    if not os.path.isdir(target_folder):
        if mkdir:
            preparedir(target_folder)
        else:
            created = preparedir(target_folder, False)
            if not created:
                raise ValueError("Failed to find %s." % target_folder)
    file_path = os.path.join(target_folder, file_name)

    if (sys.version_info < (3, 0)):
        _download_py2(url, file_path, __hdr__)
    else:
        _download_py3(url, file_path, __hdr__)


def download_file(url, file_path, mkdir=False):
    """Write a string of data to file.

    Args:
        url: A string to a valid URL.
        file_path: Full path to intended download location (e.g. c:/ladybug/testPts.pts)
        mkdir: Set to True to create the directory if doesn't exist (Default: False)
    """
    folder, fname = os.path.split(file_path)
    return download_file_by_name(url, folder, fname, mkdir)


def unzip_file(source_file, dest_dir=None, mkdir=False):
    """Unzip a compressed file.

    Args:
        source_file: Full path to a valid compressed file (e.g. c:/ladybug/testPts.zip)
        dest_dir: Target folder to extract to (e.g. c:/ladybug).
            Default is set to the same directory as the source file.
        mkdir: Set to True to create the directory if doesn't exist (Default: False)
    """
    # set default dest_dir and create it if need be.
    if dest_dir is None:
        dest_dir, fname = os.path.split(source_file)
    elif not os.path.isdir(dest_dir):
        if mkdir:
            preparedir(dest_dir)
        else:
            created = preparedir(dest_dir, False)
            if not created:
                raise ValueError("Failed to find %s." % dest_dir)

    # extract files to destination
    with zipfile.ZipFile(source_file) as zf:
        for member in zf.infolist():
            words = member.filename.split('\\')
            for word in words[:-1]:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir, ''):
                    continue
                dest_dir = os.path.join(dest_dir, word)
            zf.extract(member, dest_dir)


def csv_to_matrix(csv_file_path):
    """Load a CSV file into a Python matrix of strings.

    Args:
        csv_file_path: Full path to a valid CSV file (e.g. c:/ladybug/test.csv)
    """
    mtx = []
    with open(csv_file_path) as csv_data_file:
        for row in csv_data_file:
            mtx.append(row.split(','))
    return mtx


def csv_to_num_matrix(csv_file_path):
    """Load a CSV file consisting only of numbers into a Python matrix of floats.

    Args:
        csv_file_path: Full path to a valid CSV file (e.g. c:/ladybug/test.csv)
    """
    mtx = []
    with open(csv_file_path) as csv_data_file:
        for row in csv_data_file:
            mtx.append([float(val) for val in row.split(',')])
    return mtx
