"""strumenti per l'importazione dei dati bibliografici da file csv"""

import csv
import logging
import re

from maglib.utils.misc import BibInfo

logger = logging.getLogger("maglib.csv_import")


class MultivalueCsvDictReader(csv.DictReader):
    """supporta file csv in cui le intestazioni sono ripetibili.
    il dizionario ritornato per ogni riga ha come valori liste, un elemento
    per ogni colonna trovata per quell'intestazione"""

    def __next__(self):
        if self.line_num == 0:
            self.fieldnames
        row = next(self.reader)
        self.line_num = self.reader.line_num

        while row == []:
            row = next(self.reader)
        d = {}
        for i, value in enumerate(row[: len(self.fieldnames)]):
            fieldname = self.fieldnames[i]
            if fieldname not in d:
                d[fieldname] = []
            d[fieldname].append(value)

        lf = len(self.fieldnames)
        lr = len(row)
        if lf < lr:
            d[self.restkey] = row[lf:]

        return d


class MagInfoCsvReader(MultivalueCsvDictReader):
    """Extend MultivalueCsvDictReader with the ability to normalize fieldnames"""

    @csv.DictReader.fieldnames.getter
    def fieldnames(self):
        if self._fieldnames is None:
            try:
                row = next(self.reader)
            except StopIteration:
                pass
            else:
                self._fieldnames = list(
                    filter(None, [self._normalize_fieldname(f) for f in row])
                )
                self.line_num = self.reader.line_num
        return self._fieldnames

    def _normalize_fieldname(self, fieldname):
        raise NotImplementedError()


class BibInfoCsvReader(MagInfoCsvReader):
    """normalizza i nomi dei campi rispetto al genitore"""

    _dc_tag_regex = re.compile(r"^<?dc:(%s)>?$" % "|".join(BibInfo.dc_keys))

    def _normalize_fieldname(self, fieldname):
        f = fieldname.strip().lower()
        m = self._dc_tag_regex.match(f)
        if m:
            f = m.group(1)
        if f == "inventory_number":
            f = "inventory-number"
        return f


class CsvImportError(Exception):
    pass


class CsvBibInfoCreatorSingle(object):
    """genera le informazioni BibInfo per un mag a partire da un file csv,
    che comprende un'unica riga, oltre l'intestazione, e tutti i dati della
    riga saranno inclusi nella BibInfo. Non viene dunque considerato nessun
    campo identificativo per selezionare la riga da inserire"""

    def __init__(self, csv_file, encoding="utf-8"):
        self._encoding = encoding
        self._bib_info = None
        self._read(csv_file)

    @property
    def bib_info(self):
        """BibInfo lette dal file csv"""
        return self._bib_info

    def _read(self, csv_file):
        try:
            csv_reader = BibInfoCsvReader(open(csv_file, "r", encoding=self._encoding))
        except IOError as exc:
            raise CsvImportError(exc)

        rows = list(csv_reader)
        if not len(rows) == 1:
            raise CsvImportError(
                "please use csv with one data row for single-mag import"
            )
        self._bib_info = self._build_info_from_row(rows[0])

    def _build_info_from_row(self, row):
        bib_info = BibInfo()
        for key, values in row.items():
            if key not in bib_info.keys:
                logger.warn("ignoring unknown field %s" % key)
                continue
            for value in values:
                value = value.strip()
                if value:
                    bib_info.add_value(key, value)
        return bib_info


class CsvBibInfoCreator(object):
    """genera le informazioni BibInfo a partire da un file csv
    Richiedendo un particolare identificativo, lo cerca nel file e crea le
    informazioni dalla riga"""

    def __init__(self, identifier_field="identifier"):
        """:identifier_field: la colonna del file csv che verrà usata per
        associare gli identificativi richiesti alle righe del file csv"""
        self._identifier_field = identifier_field
        self._bib_infos = {}

    def read_file(self, csv_file, encoding="utf-8"):
        """legge un file csv e memorizza le informazioni per usarle nelle
        risposte successive
        :csv_file: path del file da caricare
        :encoding: codifica del file di testo"""
        csv_reader = BibInfoCsvReader(open(csv_file, "r", encoding=encoding))
        if self._identifier_field not in csv_reader.fieldnames:
            logger.warn(
                'csv file %s has no identifier field "%s", not loaded'
                % (csv_file, self._identifier_field)
            )
            return

        for i, row in enumerate(csv_reader):
            iD = row.get(self._identifier_field)
            if not iD or not iD[0]:
                msg = (
                    "row n %d of %s has no identifier " % (i, csv_file)
                    + 'in field "%s", skipping' % self._identifier_field
                )
                logger.warn(msg)
                continue
            iD = iD[0].strip()
            # il campo che ha come intestazione identifier_field va eliminato
            # solo se non è anche uno dei campi di BibInfo
            # if not self._identifier_field in BibInfo.keys:
            #     del row[self._identifier_field]

            if iD in self._bib_infos:
                msg = (
                    "identifier %s already present, skipping row" % iD
                    + "n %d of %s" % (i, csv_file)
                )
                logger.warn(msg)
                continue

            bib_info = self._build_info_for_row(row)
            self._bib_infos[iD] = bib_info

    def get_info(self, identifier):
        """ritorna BibInfo per un certo identifier, cercando fra le informazioni
        lette dai file csv"""
        return self._bib_infos.get(identifier)

    def _build_info_for_row(self, row):
        bib_info = BibInfo()
        for key, values in row.items():
            if key not in bib_info.keys:
                if key is not None and key != self._identifier_field:
                    logger.warn("ignoring unknown field %s" % key)
                continue
            for value in values:
                value = value.strip()
                if value:
                    bib_info.add_value(key, value)
        return bib_info
