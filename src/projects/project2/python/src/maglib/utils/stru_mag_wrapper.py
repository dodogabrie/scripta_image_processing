# -*- coding: utf-8 -*-


# FUNZIONI SULLE STRU

# livelli strutturali


class StruSeqNsReset(object):
    """imposta i sequence number sui nodi stru"""

    def __init__(self, stru_node):
        """:stru_node: elemento Stru del mag"""
        self._stru_node = stru_node

    def reset(self):
        raise NotImplementedError()


class UniqStruSeqNsReset(StruSeqNsReset):
    """imposta i sequence number in modo che ogni nodo della stru ne abbia
    uno univoco nel mag. Assegna i seq n in preordine"""

    def __init__(self, stru_node, start=1):
        super(UniqStruSeqNsReset, self).__init__(stru_node)
        self._start = start

    def reset(self):
        stru_stack = list(reversed(self._stru_node))
        seq_n = 1
        while stru_stack:
            stru = stru_stack.pop()
            stru.sequence_number.set_value(str(seq_n))
            stru_stack.extend(reversed(stru.stru))
            seq_n += 1


class UniqStruSeqNsResetLevelOrder(UniqStruSeqNsReset):
    """assegna i seq n in level-order"""

    def reset(self):
        stru_queue = list(self._stru_node)
        seq_n = 1
        while stru_queue:
            stru = stru_queue.pop(0)
            stru.sequence_number.set_value(str(seq_n))
            stru_queue.extend(stru.stru)
            seq_n += 1


class LevelsStruSeqNsReset(StruSeqNsReset):
    """imposta i seq n in modo che essi siano unici fra i fratelli del nodo"""

    def reset(self):
        for i, stru in enumerate(self._stru_node, 1):
            stru.sequence_number.set_value(str(i))
            resetter = LevelsStruSeqNsReset(stru.stru)
            resetter.reset()


def reset_stru_node_seq_n(stru_node, start=1):
    """reimposta il sequence number delle istanze stru contenute ricorsivamente
    in stru_node in modo che ogni stru abbia un sequence_number unico, e sarà
    assegnato in ordine di livello"""
    seq_n = 0
    stru_queue = list(reversed(stru_node))

    while stru_queue:
        seq_n += 1
        stru = stru_queue.pop()
        set_stru_sequence_number(stru, seq_n)
        stru_queue.extend(reversed(stru.stru))


def get_stru_sequence_number(stru_instance):
    """ritorna il sequence number di un nodo stru"""
    if stru_instance.sequence_number and stru_instance.sequence_number[0].value:
        return stru_instance.sequence_number[0].value
    else:
        return ""


def set_stru_sequence_number(stru_instance, new_sequence_number):
    """modifica il sequence_number di un nodo stru """
    if not stru_instance.sequence_number:
        stru_instance.sequence_number.add_instance()
    stru_instance.sequence_number[0].value = str(new_sequence_number)


def insert_stru(stru_node, index, stru_instance):
    """inserisce la stru stru_instance alla posizione index fra le sotto-stru
    di stru_node. I sequence_number delle sotto-stru successive a quella
    inserita vengono aumentati di 1, e il sequence_number dell'istanza
    aggiunta viene impostato al successivo del sequence_number dell'istanza
    precedente"""
    for stru in stru_node[index:]:
        set_stru_sequence_number(stru, int(get_stru_sequence_number(stru)) + 1)

    stru_node.insert(index, stru_instance)
    if index == 0:
        prev_stru_seq_num = 0
    else:
        prev_stru_seq_num = int(get_stru_sequence_number(stru_node[index - 1]))

    set_stru_sequence_number(stru_node[index], prev_stru_seq_num + 1)


def append_stru_instance(stru_node, stru_instance=None):
    """aggiunge una istanza stru ad un nodo stru, assegnandogli il
    sequence_number successivo all'ultimo assegnato
    l'istanza viene creata se non viene passata come parametro"""
    next_avaiable_sequence_number = _get_next_stru_sequence_number(stru_node)
    if stru_instance == None:
        stru_node.add_instance()
    else:
        stru_node.append(stru_instance)
    set_stru_sequence_number(stru_node[-1], next_avaiable_sequence_number)


def get_stru_nomenclature(stru_instance):
    """ritorna la nomenclatura di una stru, se presente, altrimenti ritorna stringa vuota"""
    if stru_instance.nomenclature and stru_instance.nomenclature[0].value:
        return stru_instance.nomenclature[0].value
    else:
        return ""


# elementi strutturali


def get_element_nomenclature(element_instance):
    """ritorna la nomenclatura di un element, se non presente ritorna la stringa vuota"""
    # per la nomenclatura un element è identico ad un' istanza stru
    return get_stru_nomenclature(element_instance)


def get_element_document(element_instance):
    """ritorna l'identifier del documento a cui si riferisce l'elemento strutturale element_instance
    ritorna '' se l'elemento strutturale non specifica nessun documento (e quindi
    la stru si rifersice al documento stesso"""
    if (not element_instance.identifier) or (not element_instance.identifier[0].value):
        return ""
    else:
        return element_instance.identifier[0].value


def set_element_document(element_instance, document_identifier):
    """modifica il nuovo identifier del documento a cui si riferisce l'elemento strutturale
    se document_identifier è nullo, l'identifier viene cancellato dall'elemento strutturale"""
    if not document_identifier:
        element_instance.identifier.clear()
    else:
        if not element_instance.identifier:
            element_instance.identifier.add_instance()
        element_instance.identifier[0].value = document_identifier


def get_element_resource_type(element_instance):
    """ritorna il tipo di risorsa a cui si riferisce un elemento strutturale
    se l'elemento non specifica il tipo di risorsa, seguendo lo
    standard si intende il tipo di risorsa "img" """
    if not element_instance.resource.get_value():
        return "img"
    return element_instance.resource[0].value


def set_element_resource_type(element_instance, resource_type):
    """modifica il tipo di risorsa a cui si riferisce l'elemento strutturale. se resource_type è nullo
    viene cancellato il tipo di risorsa a cui si riferisce l'elemento"""
    if not resource_type:
        element_instance.resource.clear()
    else:
        if not element_instance.resource:
            element_instance.resource.add_instance()
        element_instance.resource[0].value = resource_type


def get_element_start_seq_n(element_instance):
    """ritorna lo start sequence_number di un elemento strutturale"""
    return _get_element_seq_n(element_instance, "start")


def get_element_stop_seq_n(element_instance):
    """ritorna lo stop sequence_number di un elemento strutturale"""
    return _get_element_seq_n(element_instance, "stop")


def set_element_start_seq_n(element_instance, seq_n):
    """imposta un nuovo start sequence_number per l'elemento strutturale
    se il seq_n passato è nullo, lo start sequence_number viene rimosso"""
    return _set_element_seq_n(element_instance, seq_n, "start")


def set_element_stop_seq_n(element_instance, seq_n):
    """imposta un nuovo stop sequence_number per l'elemento strutturale
    se il seq_n passato è nullo, lo stop sequence_number viene rimosso"""
    return _set_element_seq_n(element_instance, seq_n, "stop")


def get_element_num(element_instance):
    """un element ha un attributo num, per essere ordinato.
    questo metodo ritorna quest'attributo, se c'è, oppure la stringa vuota"""
    if element_instance.num.value:
        return element_instance.num.value
    else:
        return ""


def set_element_num(element_instance, num):
    """imposta l'attributo num di un'istanza element"""
    element_instance.num.value = str(num)


def insert_element(stru_node, index, element_instance):
    stru_node.insert(index, element_instance)
    # return _insert_instance(stru_node, index, element_instance, get_element_num, set_element_num)


def append_element_instance(element_node, element_instance=None):
    if element_instance == None:
        element_node.add_instance()
    else:
        element_node.append(element_instance)


def _cmp_stru_node(anode, bnode):
    # confronto due nodi stru per sequence_number
    # -1 è minore anode, +1 è minore bnode, 0 sono uguali
    if not get_stru_sequence_number(anode):
        if get_stru_sequence_number(bnode):
            return +1
        else:
            return 0
    else:
        if get_stru_sequence_number(bnode):
            return cmp(
                int(get_stru_sequence_number(anode)),
                int(get_stru_sequence_number(bnode)),
            )
        else:
            return -1


def _get_next_stru_sequence_number(stru_node):
    """ritorna il prossimo sequence number disponibile per le istanze
    di un nodo stru"""
    max_sequence_number = 0
    for stru_instance in stru_node:
        if get_stru_sequence_number(stru_instance) and (
            int(get_stru_sequence_number(stru_instance)) > max_sequence_number
        ):
            max_sequence_number = int(get_stru_sequence_number(stru_instance))
    return max_sequence_number + 1


def _get_element_seq_n(element_instance, seq_n_type):
    # seq_n_type può essere start o stop
    if (not getattr(element_instance, seq_n_type)) or (
        not getattr(element_instance, seq_n_type)[0].sequence_number.value
    ):
        return None
    else:
        return getattr(element_instance, seq_n_type)[0].sequence_number.value


def _set_element_seq_n(element_instance, seq_n, seq_n_type):
    # seq_n_type può essere start o stop
    if not seq_n:
        getattr(element_instance, seq_n_type).clear()
    else:
        if not getattr(element_instance, seq_n_type):
            getattr(element_instance, seq_n_type).add_instance()
        getattr(element_instance, seq_n_type)[0].sequence_number.value = str(seq_n)


class StruSeqNFix(object):
    """aggiusta i sequence_number nella sezione stru in modo che dopo un
    cambiamento del seq_n delle risorse puntino ancora alle stesse risorse"""

    def __init__(self, stru, resources_type):
        """:stru: nodo con le stru del mag da aggiornare
        :resources_type: il tipo (img, doc, ocr, video, audio) risorse di cui
        questo oggetto deve gestire le modifiche"""
        self._stru = stru
        self._resources_type = resources_type

    def fix(self, seq_n_map):
        """esegue l'aggiustamento sulle stru in base ai cambiamenti nei seq_n
        mostrati dal dizionario seq_n_map, che ha come chiave il vecchio seq_n
        e come valore il nuovo seq_n.
        Se una risorsa nel cambiamento scompare oppure non c'era prima del
        cambiamento, non sarà presente come chiave nel dizionario."""
        stru_nodes = self._stru[:]

        while stru_nodes:
            stru = stru_nodes.pop(0)
            self._fix_stru_elements(stru, seq_n_map)
            for stru in stru.stru:
                stru_nodes.append(stru)

    def _fix_stru_elements(self, stru_node, seq_n_map):
        # corregge gli element dentro un singolo elemento stru
        i = 0
        while i < len(stru_node.element):
            el = stru_node.element[i]
            rsrc_type = get_element_resource_type(el)
            if rsrc_type == self._resources_type and self._element_has_range(el):

                stru_node.element.remove_instance(el)
                new_ranges = self._get_element_range(el, seq_n_map)
                for new_range in new_ranges:
                    new_el = stru_node.element.add_instance(i)
                    self._copy_element(el, new_el)
                    set_element_start_seq_n(new_el, new_range[0])
                    set_element_stop_seq_n(new_el, new_range[1])
                    i = i + 1
            else:
                i = i + 1

    def _copy_element(self, src, dst):
        # copia tutti i valori di un element in un altro
        dst.num.value = src.num.value
        dst.descr.value = src.descr.value
        for f in ("nomenclature", "identifier", "resource"):
            getattr(dst, f).set_value(getattr(src, f).get_value())

        if src.piece:
            if not dst.piece:
                dst.piece.add_instance()
            for f in (
                "year",
                "issue",
                "stpiece_per",
                "part_number",
                "part_name",
                "stpiece_vol",
            ):
                getattr(dst.piece[0], f).set_value(getattr(src.piece[0], f).get_value())

        for f in ("start", "stop"):
            if getattr(src, f):
                if not getattr(dst, f):
                    getattr(dst, f).add_instance()
                getattr(dst, f)[0].sequence_number.value = getattr(src, f)[
                    0
                ].sequence_number.value
                getattr(dst, f)[0].offset.value = getattr(src, f)[0].offset.value

    def _element_has_range(self, el):
        # dice se un element ha start e stop corretti
        start = get_element_start_seq_n(el)
        stop = get_element_stop_seq_n(el)
        if not (start and stop):
            return False
        try:
            int(start)
            int(stop)
        except ValueError:
            return False
        return True

    def _get_element_range(self, el, seq_n_map):
        # ritorna la lista di nuovi range per l'element
        el_start_seq_n = int(get_element_start_seq_n(el))
        el_stop_seq_n = int(get_element_stop_seq_n(el))

        el_seq_ns = self._range_to_seq(el_start_seq_n, el_stop_seq_n)
        new_seq_ns = sorted(
            filter(None, (seq_n_map.get(old_seq_n) for old_seq_n in el_seq_ns))
        )

        new_ranges = self._seq_to_ranges(new_seq_ns)
        return new_ranges

    @classmethod
    def _range_to_seq(self, start, stop):
        """trasforma un range x:y nella lista x...y"""
        return range(start, stop + 1)

    @classmethod
    def _seq_to_ranges(self, seq):
        """trasforma una sequenza ordinata di interi in una lista di
        intervalli rappresentati come inizio - fine (estremi inclusi)"""
        ranges = []
        cur = None
        cur_range = None
        for n in seq:
            if cur is None:
                cur_range = [n, None]
            else:
                if cur != n - 1:
                    cur_range[1] = cur
                    ranges.append(cur_range)
                    cur_range = [n, None]
            cur = n
        if cur_range:
            cur_range[1] = cur
            ranges.append(cur_range)

        return ranges
