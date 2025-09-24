# -*- coding: utf-8 -*-

"""questo modulo aiuta nella creazione di script che operano sui mag"""

import optparse
import sys

from lxml import etree

from maglib import Metadigit
from maglib.unimarc_import.base_readers import InfoReadException
from maglib.utils.misc import BibInfo


class MagScriptMain(object):
    def __init__(self):
        self._option_parser = self._build_opt_parser()

    def __call__(self, args):
        opts, args = self._option_parser.parse_args(args[1:])

        if opts.mass_mode:
            for mag_file in args:
                opts.input = mag_file # per far vedere il filename alle
                                      # operazioni
                mag_operation = self._build_mag_operation(opts, args)
                metadigit = self._open_mag(opts.input)
                if not metadigit:
                    return 1
                if not self._operate_on_mag(metadigit, opts.clean,
                                            mag_operation, mag_file):
                    return 2
        else:
            mag_operation = self._build_mag_operation(opts, args)
            if opts.input:
                metadigit = self._open_mag(opts.input)
                if not metadigit:
                    return 1
            else:
                metadigit = Metadigit()

            clean_mag = opts.input and opts.clean
            output = opts.output or sys.stdout.buffer
            if not self._operate_on_mag(metadigit, clean_mag,
                                        mag_operation, output):
                return 2

        return 0

    def _open_mag(self, mag_path):
        try:
            return Metadigit(mag_path)
        except (IOError, etree.XMLSyntaxError) as exc:
            sys.stderr.write('ERROR: can\'t open mag %s: %s\n' % (
                    mag_path, exc))
            return None

    def _build_mag_operation(self, options, args):
        """ritorna MagOperation
        :options: :args: oggetti tornati da optparse con le opzioni
        e gli argomenti da linea di comando"""
        raise NotImplementedError()

    def _build_opt_parser(self):
        """ritorna MagScriptOptionParser"""
        return MagScriptOptionParser()

    def _operate_on_mag(self, metadigit, clean_mag, mag_operation, output):
        try:
            if clean_mag:
                mag_operation.clean_mag(metadigit)
            mag_operation.do_op(metadigit)
        except MagOperationError as exc:
            sys.stderr.write('ERROR: %s\n' % str(exc))
            return False

        if mag_operation.write_mag:
            metadigit.write(output)
        return True


class MagScriptOptionParser(optparse.OptionParser):
    """parser di opzioni per script che operano su un mag"""
    def __init__(self, usage='%prog [options] [-M mag0 mag1 ...]'):
        optparse.OptionParser.__init__(self, usage=usage)
        self._required_opts = []
        self.add_option(
            '-v', '--verbose', action='store_true',
            dest='verbose', default=False)
        self.add_option(
            '-i', '--input', action='store', dest='input', default=None,
            help='file mag di input, altrimenti viene creato')
        self.add_option(
            '-o', '--output', action='store', dest='output', default=None,
            help='file di output, altrimenti sullo stdin')
        self.add_option(
            '-c', '--clean', action='store_true', dest='clean',
            default=False, help='"svuotare" il mag di input prima di operare')
        self.add_option(
            '-M', '--mass-mode', action='store_true', default=False,
            help='opera in massa su tutti i mag passati da riga di comando, '
            'eventualmente sovrascrivendoli')

    def remove_options(self, *options):
        """rimuove opzioni precedentemente aggiunte. le opzioni possono
        essere passate sia un forma lunga (--option) che breve (-o)"""
        for opt in options:
            optparse.OptionParser.remove_option(self, opt)
        self._required_opts = [
            opt for opt in self._required_opts
            if not opt.get_opt_string() in options ]
    remove_option = remove_options

    def set_options_required(self, *options):
        """imposta una opzione come richiesta, in base alla sua stringa"""
        for opt in self.option_list:
            if opt.get_opt_string() in options:
                self._required_opts.append(opt)
    set_option_required = set_options_required

    def set_options_unrequired(self, *options):
        self._required_opts = [ opt for opt in self._required_opts
                                if not opt.get_opt_string() in options ]
    set_option_unrequired = set_options_unrequired

    def add_option(self, *args, **kwargs):
        required = False
        try:
            required = kwargs.pop('required')
        except KeyError:
            pass

        opt = optparse.OptionParser.add_option(self, *args, **kwargs)
        if required:
            self._required_opts.append(opt)
        return opt

    def parse_args(self, args=None):
        opts, args = optparse.OptionParser.parse_args(self, args)

        for opt in self._required_opts:
            if opt.get_opt_string() == '--input' and opts.mass_mode:
                continue
            if not getattr(opts, opt.dest):
                self.print_help()
                self.error('option %s is required' % opt.get_opt_string())

        if opts.mass_mode:
            if opts.input or opts.output:
                self.print_help()
                self.error('don\'t use -i or -o in mass mode')
            if not args:
                self.print_help()
                self.error('please list mag in mass operation mode')
        return opts, args


class MagScriptInfoFileOptParser(MagScriptOptionParser):
    """parser di opzioni per script che leggono un file di informazioni con
    l'opzione -I"""
    def __init__(self, info_file_help='file con le informazioni',
                 usage='%prog [options]'):
        MagScriptOptionParser.__init__(self, usage)
        self.add_option(
            '-I', '--info-file', action='store', dest='info_file',
            required=True, default=None, help=info_file_help)


class MagOperation(object):
    def do_op(self, metadigit):
        raise NotImplementedError()

    def clean_mag(self, metadigit):
        pass

    @property
    def write_mag(self):
        """indica se effettuare la scrittura del mag di output"""
        return True


class MagOperationError(Exception):
    """un errore nella operazione sul mag"""
    pass


class MagInfoReader(object):
    """legge la informazioni da un file nella forma chiave = valore"""
    @classmethod
    def read_file(cls, fpath, encoding='utf-8'):
        """ritorna un dizionario con le informazioni lette"""
        f = open(fpath, 'rt')
        info = {}
        for line in f:
            if not line.strip() or line.strip().startswith('#'):
                continue
            key = line.split('=')[0].strip()
            value = line.split('=')[1]
            info[key] = cls._read_value(key, value, encoding)
        return info

    @classmethod
    def _read_value(cls, key, value, encoding):
        return value.strip()


class BibImport(object):
    """importa le informazioni da un dizionario in un nodo bib del mag.
    aggiungendole a quelle presenti. Nel dizionario possono essere presenti
    come chiavi i valori dublin core e altri della sezione bib. I valori del
    dizionario sono liste di valori da inserire"""

    @classmethod
    def do_import(cls, bib, info_dict):
        """esegue l'importazione da un dizionario nel mag"""
        for info_name, info_values in info_dict.items():
            if not info_values:
                continue

            if info_name in BibInfo.dc_keys:
                for info_value in info_values:
                    getattr(bib, info_name).add_instance().value = info_value

            elif info_name == 'level':
                bib.level.value = info_values[0]

            elif info_name in ('shelfmark', 'inventory-number', 'library'):
                if info_name == 'inventory-number':
                    info_name = 'inventory_number'
                if not bib.holdings:
                    bib.holdings.add_instance()
                if not getattr(bib.holdings[0], info_name):
                    getattr(bib.holdings[0], info_name).add_instance()
                getattr(bib.holdings[0], info_name)[0].value = info_values[0]

            elif info_name in ('year', 'issue', 'stpiece_per', 'part_number',
                               'part_name', 'stpiece_vol'):
                if not bib.piece:
                    bib.piece.add_instance()
                getattr(bib.piece[0], info_name).set_value(info_values[0])



class BibAdder(MagOperation):
    """operazione sul mag che aggiunge la sezione bib"""

    def do_op(self, metadigit):
        try:
            bib_info = self._build_bib_info()
        except InfoReadException as exc:
            raise MagOperationError(str(exc))
        if not metadigit.bib:
            metadigit.bib.add_instance()
        BibImport.do_import(metadigit.bib[0], bib_info)

    def clean_mag(self, metadigit):
        # preserva piece
        if metadigit.bib:
            piece = metadigit.bib[0].piece
        else:
            piece = None
        metadigit.bib.clear()
        if piece:
            metadigit.bib.add_instance().piece = piece

    def _build_bib_info(self):
        raise NotImplementedError()
