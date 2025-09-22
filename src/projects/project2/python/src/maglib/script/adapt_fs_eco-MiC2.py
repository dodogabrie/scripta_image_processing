#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DIVIDI_CARTELLE — GUI per ri-organizzare le risorse di un MAG (Metadigit)
secondo regole di rinomina/spostamento/copertura file.

✔ Campi: MAG input, Base Sorgente, Base Destinazione, (opz.) Basename, (opz.) Output
✔ Opzioni: Dry-run, Copia invece di spostare, Short filenames, Path style (default/fascicle), Ignora mancanti
✔ Log in tempo reale + progress bar
✔ Pronta per PyInstaller:  pyinstaller --onefile --noconsole --name dividi_cartelle dividi_cartelle_gui.py

Requisiti: maglib (con lxml) disponibile nell'ambiente.
"""

import logging
import os
import queue
import re
import shutil
import sys
import threading
from pathlib import Path
from tkinter import Tk, StringVar, BooleanVar, ttk, filedialog, messagebox, Text, END, DISABLED, NORMAL

# ------------------------- dipendenze maglib -------------------------
try:
    from maglib import Metadigit
    from maglib.utils.misc import MagResourcePath
except Exception as e:
    print(
        "ATTENZIONE: non riesco a importare 'maglib'.\n"
        "Installa/attiva l'ambiente corretto (include lxml).\n"
        f"Dettagli: {e}\n"
    )

# ------------------------- logging → Text widget ---------------------
LOGFILE = "dividi_cartelle.log"
logger = logging.getLogger("dividi_cartelle")
logger.setLevel(logging.INFO)

_queue = queue.Queue()

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            _queue.put(self.format(record))
        except Exception:
            pass

fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
qh = QueueHandler(); qh.setFormatter(fmt)
fh = logging.FileHandler(LOGFILE, encoding="utf-8"); fh.setFormatter(fmt)
logger.addHandler(qh); logger.addHandler(fh)

# ------------------------- core operation ---------------------------
class FileTransporter:
    def transport(self, old_file, new_file):
        raise NotImplementedError()

    def _prepare_dir(self, filepath):
        d = os.path.dirname(filepath)
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)

class DummyTransporter(FileTransporter):
    def transport(self, old_path, new_path):
        old_path, new_path = (os.path.normpath(p) for p in (old_path, new_path))
        logger.info("DRY-RUN: %s -> %s", old_path, new_path)

class CopyTransporter(FileTransporter):
    def __init__(self, ignore_missing):
        self._ignore_missing = ignore_missing
    def transport(self, old_path, new_path):
        self._prepare_dir(new_path)
        if self._ignore_missing and not os.path.isfile(old_path):
            logger.info("ignoring missing file %s", old_path); return
        shutil.copy2(old_path, new_path)

class MoveTransporter(FileTransporter):
    def __init__(self, ignore_missing):
        self._ignore_missing = ignore_missing
    def transport(self, old_path, new_path):
        if os.path.isfile(new_path):
            return
        if self._ignore_missing and not os.path.isfile(old_path):
            logger.info("ignoring missing file %s", old_path); return
        self._prepare_dir(new_path)
        shutil.move(old_path, new_path)

class AdaptFs:
    def __init__(self, base_src_dir, base_dst_dir, bname=None, dry_run=False, copy=False,
                 short_filenames=False, path_style="default", ignore_missing=False):
        self._bname = bname
        self._base_dst_dir = base_dst_dir
        self._base_src_dir = base_src_dir
        self._dry_run = dry_run
        self._copy = copy
        self._short_filenames = short_filenames
        self._path_style = path_style
        if self._dry_run:
            self._transporter = DummyTransporter()
        elif self._copy:
            self._transporter = CopyTransporter(ignore_missing)
        else:
            self._transporter = MoveTransporter(ignore_missing)

    def run(self, metadigit):
        bname = self._bname or self._guess_bname(metadigit)
        if not bname:
            raise RuntimeError("Impossibile determinare il basename del MAG.")

        # IMG e ALTIMG
        for i, img_node in enumerate(metadigit.img, 1):
            for img in [img_node] + list(img_node.altimg):
                self._handle_file_element(bname, i, img.file[0])
        # OCR + source
        for i, ocr in enumerate(metadigit.ocr, 1):
            self._handle_file_element(bname, i, ocr.file[0])
            if ocr.source:
                self._handle_file_element(bname, i, ocr.source[0], transport=False)

    def _handle_file_element(self, bname, index, file_el, transport=True):
        origpath = file_el.href.value
        newpath = self._build_new_path(origpath, index, bname)
        file_el.href.value = newpath
        src = os.path.normpath(os.path.join(self._base_src_dir, origpath))
        dst = os.path.normpath(os.path.join(self._base_dst_dir, newpath))
        if transport and src != dst:
            self._transporter.transport(src, dst)

    def _guess_bname(self, metadigit):
        if metadigit.bib and metadigit.bib[0].identifier:
            return metadigit.bib[0].identifier[0].value
        return None

    def _build_new_path(self, origpath, index, bname):
        old_path = MagResourcePath(origpath)
        new_dir = self._build_new_dir(bname, old_path)
        new_filename = self._build_new_filename(old_path, index, bname)
        return f"{new_dir}/{new_filename}"

    def _build_new_dir(self, bname, old_path):
        if self._path_style == "default":
            return str(Path(bname).as_posix() + "/" + old_path.resource_dirname)
        if self._path_style == "fascicle":
            m = re.match(r"^(?P<bid>.+?)_(?P<year>[0-9]{4})(?P<rest>.+)$", bname)
            if not m:
                raise RuntimeError(f'Basename non valido per path_style "fascicle": {bname}')
            # bid/year/year+rest/<resourcedir>
            return "/".join([
                m.group("bid"),
                m.group("year"),
                m.group("year") + m.group("rest"),
                old_path.resource_dirname,
            ])
        raise RuntimeError("path_style non valido (usa: default | fascicle)")

    def _build_new_filename(self, old_path: MagResourcePath, index, bname) -> str:
        file_basename = f"{index:05d}" if self._short_filenames else f"{bname}_{index:05d}"
        return f"{file_basename}.{old_path.file_extension}"

# ------------------------- GUI --------------------------------------
class App:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("dividi_cartelle — reorganizer MAG")
        self.root.geometry("820x560")

        # vars
        self.input_var = StringVar()
        self.src_var = StringVar()
        self.dst_var = StringVar()
        self.base_var = StringVar()
        self.out_var = StringVar()  # se vuoto → sovrascrive input
        self.path_style_var = StringVar(value="default")
        self.dry_var = BooleanVar(value=False)
        self.copy_var = BooleanVar(value=False)
        self.short_var = BooleanVar(value=False)
        self.ignore_var = BooleanVar(value=False)
        self.status_var = StringVar(value="Pronto")

        self._build_widgets()
        self._poll_log_queue()

    def _build_widgets(self):
        pad = 8
        frm = ttk.Frame(self.root, padding=pad); frm.pack(fill="both", expand=True)

        def row(parent):
            r = ttk.Frame(parent); r.pack(fill="x", pady=(0, pad)); return r

        r1 = row(frm)
        ttk.Label(r1, text="MAG (input .xml):", width=22).pack(side="left")
        ttk.Entry(r1, textvariable=self.input_var).pack(side="left", fill="x", expand=True, padx=(pad, pad))
        ttk.Button(r1, text="Sfoglia…", command=self._pick_input).pack(side="left")

        r2 = row(frm)
        ttk.Label(r2, text="Base sorgente (file attuali):", width=22).pack(side="left")
        ttk.Entry(r2, textvariable=self.src_var).pack(side="left", fill="x", expand=True, padx=(pad, pad))
        ttk.Button(r2, text="Sfoglia…", command=lambda: self._pick_dir(self.src_var)).pack(side="left")

        r3 = row(frm)
        ttk.Label(r3, text="Base destinazione:", width=22).pack(side="left")
        ttk.Entry(r3, textvariable=self.dst_var).pack(side="left", fill="x", expand=True, padx=(pad, pad))
        ttk.Button(r3, text="Sfoglia…", command=lambda: self._pick_dir(self.dst_var)).pack(side="left")

        r4 = row(frm)
        ttk.Label(r4, text="Basename (opz.):", width=22).pack(side="left")
        ttk.Entry(r4, textvariable=self.base_var).pack(side="left", fill="x", expand=True)

        r5 = row(frm)
        ttk.Label(r5, text="Output MAG (opz.):", width=22).pack(side="left")
        ttk.Entry(r5, textvariable=self.out_var).pack(side="left", fill="x", expand=True, padx=(pad, pad))
        ttk.Button(r5, text="Salva come…", command=self._pick_output).pack(side="left")

        r6 = row(frm)
        ttk.Label(r6, text="Path style:").pack(side="left")
        ttk.Combobox(r6, textvariable=self.path_style_var, values=["default", "fascicle"], state="readonly", width=14).pack(side="left", padx=(pad, 24))
        ttk.Checkbutton(r6, text="Dry run (solo log)", variable=self.dry_var).pack(side="left")
        ttk.Checkbutton(r6, text="Copia invece di spostare", variable=self.copy_var).pack(side="left", padx=(pad,0))

        r7 = row(frm)
        ttk.Checkbutton(r7, text="Short filenames", variable=self.short_var).pack(side="left")
        ttk.Checkbutton(r7, text="Ignora file mancanti", variable=self.ignore_var).pack(side="left", padx=(pad,0))

        r8 = row(frm)
        self.pbar = ttk.Progressbar(r8, mode="indeterminate"); self.pbar.pack(side="left", fill="x", expand=True)
        ttk.Button(r8, text="Esegui", command=self._run).pack(side="left", padx=(pad,0))
        ttk.Label(r8, textvariable=self.status_var, width=16, anchor="e").pack(side="left", padx=(pad, 0))

        ttk.Label(frm, text="Log:").pack(anchor="w")
        self.log = Text(frm, height=16, wrap="word"); self.log.pack(fill="both", expand=True); self.log.config(state=DISABLED)

    # --- pickers ---
    def _pick_input(self):
        f = filedialog.askopenfilename(title="Scegli MAG (.xml)", filetypes=[("XML","*.xml"), ("Tutti i file","*.*")])
        if f: self.input_var.set(f)
    def _pick_output(self):
        init = self.input_var.get().strip() or os.getcwd()
        f = filedialog.asksaveasfilename(title="Salva MAG come…", defaultextension=".xml", initialdir=os.path.dirname(init), filetypes=[("XML","*.xml")])
        if f: self.out_var.set(f)
    def _pick_dir(self, var):
        d = filedialog.askdirectory(title="Seleziona cartella")
        if d: var.set(d)

    # --- run ---
    def _run(self):
        input_xml = self.input_var.get().strip()
        base_src = self.src_var.get().strip() or os.path.dirname(input_xml)
        base_dst = self.dst_var.get().strip() or os.path.dirname(input_xml)
        if not input_xml or not os.path.isfile(input_xml):
            messagebox.showwarning("Attenzione", "Seleziona un file MAG (.xml) valido."); return
        if not os.path.isdir(base_src):
            messagebox.showwarning("Attenzione", "Base sorgente non valida."); return
        if not os.path.isdir(base_dst):
            messagebox.showwarning("Attenzione", "Base destinazione non valida."); return

        self.status_var.set("In esecuzione…"); self.pbar.start(10)
        t = threading.Thread(target=self._do_work, args=(input_xml, base_src, base_dst), daemon=True)
        t.start()

    def _do_work(self, input_xml, base_src, base_dst):
        try:
            m = Metadigit(input_xml)
            bname = self.base_var.get().strip() or None
            op = AdaptFs(
                base_src_dir=base_src,
                base_dst_dir=base_dst,
                bname=bname,
                dry_run=self.dry_var.get(),
                copy=self.copy_var.get(),
                short_filenames=self.short_var.get(),
                path_style=self.path_style_var.get(),
                ignore_missing=self.ignore_var.get(),
            )
            op.run(m)

            # Scrivi MAG se non è dry-run
            if not self.dry_var.get():
                out = self.out_var.get().strip() or input_xml
                m.write(out)
                logger.info("MAG scritto in: %s", out)
            else:
                logger.info("Dry-run: nessuna scrittura del MAG.")

            logger.info("Operazione completata.")
        except Exception as e:
            logger.exception("Errore: %s", e)
        finally:
            self.root.after(0, self._done)

    def _done(self):
        self.pbar.stop(); self.status_var.set("Pronto")

    # --- log pump ---
    def _append_log(self, text):
        self.log.config(state=NORMAL)
        self.log.insert(END, text + "\n")
        self.log.see(END)
        self.log.config(state=DISABLED)
    def _poll_log_queue(self):
        try:
            while True:
                self._append_log(_queue.get_nowait())
        except queue.Empty:
            pass
        self.root.after(120, self._poll_log_queue)

# ------------------------- main -------------------------------------

def main():
    root = Tk()
    try:
        ttk.Style(root).theme_use("clam")
    except Exception:
        pass
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
