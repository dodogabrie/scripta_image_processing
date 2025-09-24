# -*- coding: utf-8 -*-



"""Questo package si occupa di importare le risorse (immagini, video, audio,
documenti) all'interno del documento MAG.
Si presuppone che il MAG abbia una directory in cui sono contenute le sue
risorse, ed ogni tipo di risorsa in una sotto directory. Le risorse contenute
nella stessa sotto directory si suppongono omogenee per tipo (img, video, ....)
ed eventualmente anche per appartenenza allo stesso gruppo di risorse per i tipi
che lo prevedono (img, audio, video)
Si può specificare in che sotto-directory cercare le risorse e le estensioni dei
file da considerare. Per i tipi che lo prevedono (img, audio, video) si
possono indicare directory che contengono formati alternativi delle immagini
(altimg, video/audio proxy) ciascuna directory riferita ad una directory con un
formato principale

Il modulo dir_import contiene gli importatori di più basso livello, che operano
su singole directory, indicate esplicitamente.

Il modulo glob_import permette invece di importare 




Ci sono tre gerarchie di classi utilizzabili:







La terza opzione prevede un ulteriore layer di astrazione sulle classi
precedenti.
È nel modulo wizard.py.
Si utilizzando le derivate di ImportOptions per descrivere le
opzioni di importazione, e le derivate di ImportRunner per eseguire
l'importazione.

Es.
>> options = ImageImportOptions(sort=True, path_levels=2)
>> runner = ImportRunner(metadigit=metadigit, mag_path='/srv/data',
                         options=options)
>> runner.run()
>> print runner.message
"""
