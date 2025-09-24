# -*- coding: utf-8 -*-

"""modulo con strumenti di utilità per i test"""

import functools
import os
import shutil
import tempfile
from os.path import join

from maglib import Metadigit
from maglib.utils.resources_import.wizard import (ImageImportOptions,
                                                  ImageImportRunner)


class MagDir(object):
    def __init__(self, basename, subdirs, n_files):
        self._basename = basename
        self._tmppath = tempfile.mkdtemp()

        os.makedirs(join(self._tmppath, basename))

        for subdir, extension in subdirs:
            os.mkdir(join(self._tmppath, basename, subdir))
            for c in range(1, n_files + 1):
                filename = '{}_{:04d}.{}'.format(basename, c, extension)
                self._touch(join(self._tmppath, basename, subdir, filename))

    @property
    def path(self):
        """ritorna il path che contiene le risorse del mag"""
        return join(self._tmppath, self._basename)

    @property
    def basepath(self):
        """ritorna il path che contiene la directory delle risorse del mag"""
        return self._tmppath

    @property
    def basename(self):
        return self._basename

    def destroy(self):
        shutil.rmtree(self._tmppath)

    def _touch(self, path):
        open(path, 'w')

def mag_dir_test(*mag_dir_args, **mag_dir_kwargs):
    """decoratore per un test che utilizza una MagDir"""
    def test_decorator(func):
        @functools.wraps(func)
        def wrapper(*func_args, **func_kwargs):
            test_mag_dir = MagDir(*mag_dir_args, **mag_dir_kwargs)
            func_args += (test_mag_dir,)
            try:
                func(*func_args, **func_kwargs)
            except Exception:
                raise
            finally:
                test_mag_dir.destroy()
        return wrapper
    return test_decorator


def mag_test(basename, subdirs, n_files):
    """decoratore per un test che utilizza un mag con delle immagini"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*func_args, **func_kwargs):
            test_mag_dir = MagDir(basename, subdirs, n_files)
            metadigit = Metadigit()
            subdir_names = [sd[0] for sd in subdirs]
            import_opts = ImageImportOptions(
                alt_subdirs=subdir_names[1:],
                subdirs=subdir_names[:1],
                dotslash=True)
            ImageImportRunner(metadigit, test_mag_dir.path, import_opts).run()
            func_args += (metadigit, test_mag_dir)
            try:
                func(*func_args, **func_kwargs)
            except Exception:
                raise
            finally:
                test_mag_dir.destroy()
        return wrapper
    return decorator
