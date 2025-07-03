from django.db import models
import hashlib
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import m2m_changed, pre_delete
from django.dispatch import receiver
import json

class Documento(models.Model):
    # Identificativo univoco del documento costruito nel modo seguente: “codicesede”-“codicefascicolo”-“codiceunivoco”
    id_doc = models.CharField(max_length=80, primary_key=True)
    # hash del documento calcolato con l’algoritmo di hash specificato
    hash_doc = models.CharField(max_length=80, editable=False)
    # data di creazione dell'hash
    hash_algorithm = models.CharField(max_length=30, default='sha256', editable=False)

    pdf_path = models.CharField(
        max_length=255,
        verbose_name="Percorso PDF",
        help_text="Percorso relativo del file PDF associato al documento (es. scan/...) per uso web.",
        null=True, blank=True,
        default=None
    )
    full_pdf_path = models.CharField(
        max_length=512,
        verbose_name="Percorso PDF assoluto",
        help_text="Percorso assoluto del file PDF sul filesystem (per uso export, non per il frontend)",
        null=True, blank=True,
        default=None
    )

    MODALITIES = (
        ('a', 'doc nativo informatico'),
        ('b', 'acquisizione di un doc informatico per via telematica oppure scansioni di doc analoghi (prodotto della digtizzazione degli archivi)'),
        ('c', 'informazioni risultanti da transazioni o processi informatici'),
    )
    modality = models.CharField(verbose_name="modalità", max_length=30, choices=MODALITIES)

    # Tipologia documentale
    type_doc = models.IntegerField(
        verbose_name="tipologia_doc",
        choices=[(i, str(i)) for i in range(1, 16)]
    )

    attachments = models.IntegerField(verbose_name="allegati", default=0)

    pages = models.IntegerField(verbose_name="Numero di pagine", default=0)

    confidential = models.BooleanField(verbose_name="riservato", default=False)

    digital_native = models.BooleanField(verbose_name="nativo informatico", default=False)

    FORMAT_CHOICES = (
        ('1', 'PDF/A'),
        ('2', 'Altro'),
    )
    id_format = models.CharField(max_length=80, verbose_name="formato", choices=FORMAT_CHOICES)
    id_fascicolo = models.CharField(max_length=80, verbose_name="id_fascicolo", blank=True, null=True)


    last_edit_date = models.DateTimeField(auto_now_add=True)

    # Nuovo campo per testo libero nei soggetti
    free_fields_subjects = models.BooleanField(default=False, verbose_name="Testo libero soggetti")

    def __str__(self):
        return self.id_doc

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documenti"
        # id_doc è già primary_key, quindi unico


    def save(self, *args, **kwargs):
        algo = self.hash_algorithm or 'sha256'
        try:
            hash_func = getattr(hashlib, algo)
        except AttributeError:
            hash_func = hashlib.sha256
            self.hash_algorithm = 'sha256'
        self.hash_doc = hash_func(self.id_doc.encode('utf-8')).hexdigest()
        # Aggiorna last_edit_date ad ogni salvataggio
        self.last_edit_date = timezone.now()
        super().save(*args, **kwargs)


# -----------------------------------------------------------------------------#

class RegistrationData(models.Model):
    documento = models.OneToOneField(
        Documento,
        related_name='registration_data',
        on_delete=models.CASCADE,
        verbose_name="documento"
    )
    FLUX_TYPES = (
        ('U', 'in uscita'),
        ('E', 'in entrata'),
        ('I', 'interno'),
    )

    flux_type = models.CharField(max_length=10, verbose_name="tipologia_flusso", choices=FLUX_TYPES, default='I')

    REGISTER_TYPES = (
        ('N', 'Nessuno'),
        ('O', 'Protocollo Ordinario'),
        ('E', 'Protocollo Emergenza'),
        ("R", 'Protocollo Riservato'),
        ("S", 'Repertorio'),
    )
    register_type = models.CharField(max_length=10, verbose_name="tipo_registro", choices=REGISTER_TYPES, default='N')

    # Split into date and time fields
    registration_date = models.DateField(verbose_name="Data registrazione", blank=True, null=True)
    registration_time = models.TimeField(verbose_name="Ora registrazione", blank=True, null=True)

    doc_number = models.CharField(max_length=80, verbose_name="numero_doc", blank=True, null=True)

    register_id = models.CharField(max_length=80, verbose_name="id_registro", blank=True, null=True)

    class Meta:
        verbose_name = "Dati di registrazione"
        verbose_name_plural = "Dati di registrazione"

# -----------------------------------------------------------------------------#
class DescriptiveKey(models.Model):
    documento = models.OneToOneField(
        Documento,
        related_name='descriptive_key',
        on_delete=models.CASCADE,
        verbose_name="documento"
    )
    obj = models.ForeignKey("main.DocumentType", on_delete=models.PROTECT, verbose_name="oggetto")

    # Add property for subcategory_code
    @property
    def subcategory_code(self):
        return self.obj.subcategory_code if self.obj else None

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.persons.count() > 5:
            raise ValidationError("Una chiave descrittiva può essere associata a un massimo di 5 persone.")

    class Meta:
        verbose_name = "Chiave descrittiva"
        verbose_name_plural = "Chiavi descrittive"



class Person(models.Model):
    descriptive_keys = models.ManyToManyField(
        DescriptiveKey,
        related_name='persons',
        verbose_name="chiavi_descrittive",
        blank=True 
    )
    # Nome e cognome della persona
    name = models.CharField(max_length=80, verbose_name="nome")
    surname = models.CharField(max_length=80, verbose_name="cognome")
    resident = models.BooleanField(verbose_name="residente")
    italian = models.BooleanField(verbose_name="italiano")

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.descriptive_keys.count() > 5 and not self.pk:
            raise ValidationError("Una persona può essere associata a un massimo di 5 chiavi descrittive.")

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Persone"

# -----------------------------------------------------------------------------#

class Subjects(models.Model):
    soggetti_documento = models.ForeignKey(
        Documento,
        related_name='subjects_set',
        on_delete=models.CASCADE,
        verbose_name="documento"
    )
    ROLES = (
        ('author', 'Autore'),
        ('recipient', 'Destinatario'),
        ('sender', 'Mittente'),
        ('registrant', 'Soggetto che effettua la registrazione'),
        ('other', 'Altro'),
    )
    role = models.CharField(max_length=80, verbose_name="ruolo", choices=ROLES)

    TYPES = (
        ("", "----"),
        ('PAI', 'Pubblica Amministrazione Italiana'),
        ('PF', 'Persona Fisica'),
        ('PG', 'Organizzazione'),
        ('PAE', 'Pubblica Amministrazione Estera'),
    )
    subject_type = models.CharField(max_length=80, verbose_name="tipo_soggetto", choices=TYPES, blank=True, null=True, default="")

    subfield1 = models.CharField(verbose_name="sottocampo1", max_length=80,blank=True, null=True)
    subfield2 = models.CharField(verbose_name="sottocampo2", max_length=80, blank=True, null=True)

    class Meta:
        verbose_name = "Soggetto"
        verbose_name_plural = "Soggetti"


# -----------------------------------------------------------------------------#

class Verification(models.Model):
    documento = models.OneToOneField(
        Documento,
        related_name='verification',
        on_delete=models.CASCADE,
        verbose_name="documento"
    )
    # firmato digitalmente
    signed = models.BooleanField(verbose_name="firmato_digitalmente", default=False)
    # sigillato eln
    sealed = models.BooleanField(verbose_name="sigillato_eln", default=False)
    # marcatura temporale
    marked = models.BooleanField(verbose_name="marcatura_temporale", default=False)
    # conforme
    compliant = models.BooleanField(verbose_name="conforme", default=False)

    class Meta:
        verbose_name = "Verifica"
        verbose_name_plural = "Verifiche"


# -----------------------------------------------------------------------------#

class DocumentType(models.Model):
    category_code = models.IntegerField(verbose_name="codice_categoria")
    category = models.CharField(max_length=80, verbose_name="Tipologia")
    subcategory_code = models.CharField(max_length=4, verbose_name="Subcodice")
    subcategory = models.CharField(max_length=80, verbose_name="Sottotipologia")

    class Meta:
        verbose_name = "Tipologia documentale"
        verbose_name_plural = "Tipologie documentali"
        unique_together = ('category_code', 'subcategory_code')

    def __str__(self):
        return f"{self.category_code}.{self.subcategory_code} - {self.category}:{self.subcategory}"



# -----------------------------------------------------------------------------#


class Aggregato(models.Model):
    id_agg = models.CharField(max_length=80, unique=True, verbose_name="ID aggregato")
    impronta = models.CharField(max_length=128, verbose_name="Hash documento (SHA-512)")
    algoritmo = models.CharField(max_length=20, default="SHA-512", verbose_name="Algoritmo hash")
    note = models.CharField(max_length=516, blank=True, null=True, verbose_name="Note")

    # Nuovo campo export a tre stati
    EXPORT_STATES = (
        (0, "Non processato"),
        (1, "In esportazione"),
        (2, "Recupero"),
        (3, "Esportato"),
    )
    export = models.IntegerField(choices=EXPORT_STATES, default=0, verbose_name="Stato export")

    STATI = (
        ("creato", "Creato"),
        ("indicizzato", "Indicizzato"),
        ("normalizzato", "Normalizzato"),
        ("acquisito", "Acquisito"),
        ("metadatato", "Metadatato"),
        ("ricomposto", "Ricomposto"),
    )
    stato = models.CharField(
        max_length=20,
        choices=STATI,
        default="creato",
        verbose_name="Stato aggregato"
    )

    TIPO_CHOICES = (
        ("fascicolo", "Fascicolo"),
        ("serie_documentale", "Serie documentale"),
        ("serie_fascicoli", "Serie di fascicoli"),
    )

    tipo_agg = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default="fascicolo",
        verbose_name="Tipo aggregazione"
    )

    TIPOLOGIE = (
        ('affare', 'Affare'),
        ('attività', 'Attività'),
        ('persona fisica', 'Persona fisica'),
        ('persona giuridica', 'Persona giuridica'),
        ('procedimento', 'Procedimento amministrativo'),
    )
    tipologia_fascicolo = models.CharField(max_length=30, choices=TIPOLOGIE, default='persona fisica')

    data_apertura = models.DateField(verbose_name="Data apertura")

    # Chiusura
    data_chiusura = models.DateField(blank=True, null=True)

    # Indice doc
    id_doc = models.CharField(max_length=80, blank=True, null=True)
    posizione_fisica = models.CharField(max_length=100, blank=True, null=True)
    id_oggetto = models.CharField(max_length=10, blank=True, null=True)

    FORMAT_CHOICES = (
        ('1', 'PDF/A'),
        ('2', 'Altro'),
    )
    id_format = models.CharField(max_length=80, verbose_name="formato", choices=FORMAT_CHOICES)

    last_edit_date = models.DateTimeField(auto_now=True, verbose_name="Data ultima modifica")

    class Meta:
        verbose_name = "Aggregato"
        verbose_name_plural = "Aggregati"

    def __str__(self):
        return self.id_agg

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        is_update = self.pk is not None
        old_stato = None
        if is_update:
            try:
                old = Aggregato.objects.get(pk=self.pk)
                old_stato = old.stato
            except Aggregato.DoesNotExist:
                old_stato = None
        # Non toccare export se già esportato
        if self.export == 3 and old_stato == self.stato:
            pass  # Non modificare export se già esportato e non è cambiato lo stato
        elif self.stato == "ricomposto" and old_stato != "ricomposto":  # Se lo stato diventa "ricomposto", imposta export a 1
            self.export = 1
        elif self.export != 2 and old_stato != self.stato:  # Se non è in stato di recupero e cambia lo stato, resetta export
            self.export = 0
        super().save(*args, **kwargs)
        # Aggiorna i contatori in ExportSettings
        try:
            from main.models import ExportSettings
            ExportSettings.update_counts()
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        # Cancella tutti i documenti associati tramite DocIndex.docs
        for docindex in self.doc_index.all():
            # Salva i documenti da eliminare prima di cancellare la relazione
            docs_to_delete = list(docindex.docs.all())
            docindex.docs.clear()
            for doc in docs_to_delete:
                doc.delete()
        super().delete(*args, **kwargs)


# -----------------------------------------------------------------------------#

class DocIndex(models.Model):
    aggregato = models.ForeignKey(
        Aggregato,
        related_name='doc_index',
        on_delete=models.CASCADE,
        verbose_name="Aggregato"
    )
    tipo_doc = models.CharField(max_length=50, default="documento informatico", verbose_name="Tipo documento")
    docs = models.ManyToManyField(
        Documento,
        related_name='doc_indexes',
        verbose_name="Documenti",
        blank=True
    )


class AggregationSubjects(models.Model):
    soggetto_aggregato = models.ForeignKey(
        Aggregato,
        related_name='subjects',
        on_delete=models.CASCADE,
        verbose_name="aggregato"
    )

    RUOLI = (
        ('amministrazione_titolare', 'Amministrazione titolare'),
        ('amministrazione_partecipante', 'Amministrazioni partecipanti'),
        ('assegnatario', 'Assegnatario'),
        ('intestatario_pf', 'Soggetto intestatario persona fisica'),
        ('intestatario_pg', 'Soggetto intestatario persona giuridica'),
        ('rup', 'RUP'),
    )

    TIPO_SOGGETTI = (
        ('PAI', 'Pubblica Amministrazione Italiana'),
        ('PAE', 'Pubblica Amministrazione Estera'),
        ('PF', 'Persona Fisica'),
        ('PG', 'Organizzazione'),
    )

    ruolo = models.CharField(
        max_length=30,
        choices=RUOLI,
        default='amministrazione_titolare',
        verbose_name="Ruolo"
    )

    tipo_soggetto = models.CharField(
        max_length=3,
        choices=TIPO_SOGGETTI,
        default='PAI',
        verbose_name="Tipo soggetto"
    )

    pai = models.CharField(
        max_length=100,
        default="CORDOBA (CONSOLATO GENERALE)",
        verbose_name="PAI"
    )

    class Meta:
        verbose_name = "Soggetto dell'aggregato"
        verbose_name_plural = "Soggetti dell'aggregato"


# -----------------------------------------------------------------------------#

class Classificazione(models.Model):
    classificazione_aggregato = models.ForeignKey(
        Aggregato,
        related_name='classificazione',
        on_delete=models.CASCADE,
        verbose_name="aggregato"
    )

    codice = models.CharField(max_length=80, unique=False, blank=True, null=True, default="", verbose_name="Indice di classificazione")
    DESCRIPTION_TEXT = "La classificazione si basa sull'ordinamento annuale progressivo dei fascicoli."
    descrizione = models.CharField(max_length=255, blank=True, null=True, default="", verbose_name="Descrizione", help_text=DESCRIPTION_TEXT)
    progressivo = models.IntegerField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        """
        Gestisce il calcolo automatico del progressivo per le classificazioni.
        Aggiorna anche i progressivi delle classificazioni successive se necessario.
        """
        if not self.pk:  # Solo per nuove istanze
            anno_apertura = self.classificazione_aggregato.data_apertura.year
            data_apertura = self.classificazione_aggregato.data_apertura

            # Trova tutte le classificazioni dello stesso anno ordinate per data_apertura e id
            classificazioni_anno = Classificazione.objects.filter(
                classificazione_aggregato__data_apertura__year=anno_apertura
            ).order_by('classificazione_aggregato__data_apertura', 'id')

            # Trova la posizione dove inserire la nuova classificazione
            pos = 0
            for c in classificazioni_anno:
                if (c.classificazione_aggregato.data_apertura < data_apertura or
                    (c.classificazione_aggregato.data_apertura == data_apertura and c.id < (self.id or 0))):
                    pos += 1
                else:
                    break
            self.progressivo = pos + 1

            super().save(*args, **kwargs)

            # Aggiorna i progressivi delle classificazioni successive
            classificazioni_da_aggiornare = Classificazione.objects.filter(
                classificazione_aggregato__data_apertura__year=anno_apertura
            ).order_by('classificazione_aggregato__data_apertura', 'id')

            for idx, c in enumerate(classificazioni_da_aggiornare, start=1):
                if c.progressivo != idx:
                    c.progressivo = idx
                    c.save(update_fields=['progressivo'])
        else:
            super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Classificazione"
        verbose_name_plural = "Classificazioni"
        ordering = ['classificazione_aggregato__data_apertura', 'id']

    def __str__(self):
        return self.codice or ""

# -----------------------------------------------------------------------------#

class ChiaveDescrittiva(models.Model):
    aggregato = models.OneToOneField(
        Aggregato,
        on_delete=models.CASCADE,
        related_name='chiave_descrittiva',
        verbose_name="aggregato"
    )

    oggetto = models.CharField(max_length=100, verbose_name="Oggetto")

    class Meta:
        verbose_name = "Chiave descrittiva"
        verbose_name_plural = "Chiavi descrittive"

    def __str__(self):
        return f"Oggetto: {self.oggetto}"


class ParolaChiave(models.Model):
    chiave = models.ForeignKey(
        ChiaveDescrittiva,
        related_name='parolechiave',
        on_delete=models.CASCADE,
        verbose_name="chiave descrittiva"
    )
    testo = models.CharField(max_length=100, verbose_name="Parola chiave")

    class Meta:
        verbose_name = "Parola chiave"
        verbose_name_plural = "Parole chiave"

def get_choices_display(field):
    """
    Ritorna una lista di dict {'value': ..., 'label': ..., 'help': ...} per un campo choices di un modello.
    La sigla (value) viene mostrata come label, la descrizione lunga come help.
    """
    return [{'value': v, 'label': v, 'help': l} for v, l in field.choices]


class SubjectRule(models.Model):
    role = models.CharField(max_length=50, choices=Subjects.ROLES)
    subject_type = models.CharField(max_length=50, choices=Subjects.TYPES)
    subfield1_required = models.BooleanField(default=False)
    subfield1_label = models.CharField(max_length=100, blank=True)
    subfield2_required = models.BooleanField(default=False)
    subfield2_label = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ('role', 'subject_type')
        verbose_name = "Regola soggetto"
        verbose_name_plural = "Regole soggetti"

    def as_dict(self):
        return {
            "role": self.role,
            "subject_type": self.subject_type,
            "subfield1_required": self.subfield1_required,
            "subfield1_label": self.subfield1_label,
            "subfield2_required": self.subfield2_required,
            "subfield2_label": self.subfield2_label,
        }


class Logs(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    aggregato = models.ForeignKey(
        Aggregato,
        related_name='logs',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    stato_iniziale = models.CharField(max_length=20, blank=True, null=True)
    stato_finale = models.CharField(max_length=20, blank=True, null=True)
    details = models.TextField()

    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} | {self.user}: {self.aggregato} - {self.stato_iniziale} -> {self.stato_finale}"

# -----------------------------------------------------------------------------#

class FileStorage(models.Model):
    descrizione = models.CharField(max_length=255, verbose_name="Descrizione")
    path_locale = models.CharField(
        max_length=512,
        verbose_name="Path locale sul server",
        help_text="Inserisci il percorso assoluto o relativo del file/directory sul server. Es: /var/data/file.txt"
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        verbose_name = "File in storage"
        verbose_name_plural = "Files in storage"

    def __str__(self):
        return f"{self.descrizione} ({self.path_locale})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.descrizione)
        super().save(*args, **kwargs)


# -----------------------------------------------------------------------------#

class BatchImportReport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    batch_name = models.CharField(max_length=255, help_text="Nome o identificativo del batch/csv elaborato")
    status = models.CharField(max_length=20, choices=[('success','Successo'),('partial','Parziale'),('error','Errore')], default='success')
    note = models.TextField(blank=True, help_text="Note generali o log del batch")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='batch_imports', help_text="Utente che ha eseguito l'import batch")
    csv_files = models.TextField(blank=True, help_text="Lista dei file CSV importati in questo batch, separati da virgola")

    def csv_files_list(self):
        """
        Restituisce una lista dei file CSV importati, se presenti.
        """
        if self.csv_files:
            return [f.strip() for f in self.csv_files.split(',')]
        return []

    def set_csv_files(self, files):
        """
        Imposta la lista dei file CSV importati come stringa separata da virgola.
        """
        if isinstance(files, list):
            self.csv_files = ', '.join(files)
        elif isinstance(files, str):
            self.csv_files = files
        else:
            raise ValueError("files deve essere una lista o una stringa")

    class Meta:
        verbose_name = "Report import batch"
        verbose_name_plural = "Report import batch"
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch {self.batch_name} ({self.created_at:%Y-%m-%d %H:%M}) - {self.status}"

class BatchImportFascicoloReport(models.Model):
    batch = models.ForeignKey(BatchImportReport, related_name='fascicoli', on_delete=models.CASCADE)
    fascicolo_pk = models.IntegerField(null=True, blank=True, help_text="PK fascicolo nel DB")
    fascicolo_id = models.CharField(max_length=80, help_text="ID fascicolo analizzato")
    status = models.CharField(max_length=20, choices=[('success','Successo'),('partial','Parziale'),('error','Errore')], default='success')
    db_doc_pks = models.TextField(blank=True, help_text="Lista di PK dei documenti nel DB")
    db_doc_ids = models.TextField(blank=True, help_text="Lista di id_doc dei documenti nel DB")
    csv_doc_ids = models.TextField(blank=True, help_text="Lista di id_doc trovati nel CSV")
    matched_doc_pks = models.TextField(blank=True, help_text="PK dei documenti che corrispondono tra DB e CSV")
    matched_doc_ids = models.TextField(blank=True, help_text="id_doc che corrispondono tra DB e CSV")
    missing_in_db_ids = models.TextField(blank=True, help_text="id_doc presenti nel CSV ma non nel DB")
    missing_in_db_pks = models.TextField(blank=True, help_text="PK dei documenti presenti nel CSV ma non nel DB")
    missing_in_csv_ids = models.TextField(blank=True, help_text="id_doc presenti nel DB ma non nel CSV")
    missing_in_csv_pks = models.TextField(blank=True, help_text="PK dei documenti presenti nel DB ma non nel CSV")
    errors = models.TextField(blank=True, help_text="Dettagli errori riscontrati")
    note = models.TextField(blank=True, help_text="Note aggiuntive")

    @property
    def errors_list(self):
        """
        Restituisce sempre una lista di errori (deserializzando il campo errors).
        Se il campo è vuoto o non è un JSON valido, restituisce una lista vuota.
        """
        if not self.errors:
            return []
        try:
            val = json.loads(self.errors)
            if isinstance(val, list):
                return val
            return [val]
        except Exception:
            return []

    @errors_list.setter
    def errors_list(self, value):
        """
        Imposta il campo errors serializzando la lista in JSON.
        """
        if value is None:
            self.errors = ""
        else:
            self.errors = json.dumps(value, ensure_ascii=False)

    def save(self, *args, **kwargs):
        """
        Assicura che errors sia sempre serializzato come JSON se è una lista o dict.
        """
        if isinstance(self.errors, (list, dict)):
            self.errors = json.dumps(self.errors, ensure_ascii=False)
        super().save(*args, **kwargs)

    def add_error(self, error):
        """
        Aggiunge un errore alla lista e aggiorna il campo errors.
        """
        errors = self.errors_list
        errors.append(error)
        self.errors_list = errors

    class Meta:
        verbose_name = "Report fascicolo import batch"
        verbose_name_plural = "Report fascicoli import batch"
        ordering = ['fascicolo_id']

    def __str__(self):
        return f"Fascicolo {self.fascicolo_id} - {self.status} (Batch {self.batch_id})"


class ExportSettings(models.Model):
    consegna_threshold = models.PositiveIntegerField(default=1, verbose_name="Threshold consegna")
    updated_at = models.DateTimeField(auto_now=True)
    fascicoli_in_recupero = models.PositiveIntegerField(default=0, verbose_name="Fascicoli in recupero")
    fascicoli_in_export = models.PositiveIntegerField(default=0, verbose_name="Fascicoli in esportazione")

    class Meta:
        verbose_name = "Impostazioni export"
        verbose_name_plural = "Impostazioni export"

    def __str__(self):
        return f"Threshold consegna: {self.consegna_threshold} | In recupero: {self.fascicoli_in_recupero} | In export: {self.fascicoli_in_export}"

    @classmethod
    def update_counts(cls):
        from main.models import Aggregato
        in_recupero = Aggregato.objects.filter(export=2).count()
        in_export = Aggregato.objects.filter(export=1).count()
        obj, _ = cls.objects.get_or_create(pk=1)
        obj.fascicoli_in_recupero = in_recupero
        obj.fascicoli_in_export = in_export
        obj.save(update_fields=["fascicoli_in_recupero", "fascicoli_in_export", "updated_at"])

@receiver(m2m_changed, sender=DocIndex.docs.through)
def sync_id_fascicolo_with_docs(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Sincronizza il campo id_fascicolo dei documenti quando la relazione M2M viene modificata.
    """
    if action not in ["post_add", "post_remove", "post_clear"]:
        return
    print(f"[m2m_changed] Azione: {action} su DocIndex pk={instance.pk} (agg={instance.aggregato.id_agg})")
    from main.models import Documento
    current_doc_ids = set(instance.docs.values_list('id_doc', flat=True))
    print(f"[m2m_changed] Documenti attualmente associati: {current_doc_ids}")
    # Setta id_fascicolo = aggregato per i documenti attualmente associati
    for doc in instance.docs.all():
        if doc.id_fascicolo != instance.aggregato.id_agg:
            print(f"[m2m_changed] Setto id_fascicolo={instance.aggregato.id_agg} su doc {doc.id_doc} (prima era {doc.id_fascicolo})")
            doc.id_fascicolo = instance.aggregato.id_agg
            doc.save(update_fields=["id_fascicolo"])
    # Svuota id_fascicolo per i documenti che prima erano associati ma ora non più
    docs_prev = Documento.objects.filter(id_fascicolo=instance.aggregato.id_agg)
    for doc in docs_prev:
        if doc.id_doc not in current_doc_ids:
            print(f"[m2m_changed] Rimuovo id_fascicolo da doc {doc.id_doc} (era associato ma ora non più)")
            doc.id_fascicolo = ""
            doc.save(update_fields=["id_fascicolo"])
    print(f"[m2m_changed] Fine sync DocIndex pk={instance.pk}")

# -----------------------------------------------------------------------------#

class ExportConsegnaReport(models.Model):
    nome_consegna = models.CharField(max_length=255, help_text="Nome o identificativo della consegna")
    directory_consegna = models.CharField(max_length=512, help_text="Percorso della directory di consegna")
    error_message = models.TextField(blank=True, null=True, help_text="Eventuali messaggi di errore")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='export_consegna', help_text="Utente che effettua la consegna")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Report consegna export"
        verbose_name_plural = "Report consegne export"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nome_consegna} ({self.created_at:%Y-%m-%d %H:%M})"

# -----------------------------------------------------------------------------#

class CsvImportato(models.Model):
    path = models.CharField(max_length=512, unique=True, verbose_name="Percorso CSV importato")
    last_modified = models.DateTimeField(verbose_name="Ultima modifica file", null=True, blank=True)
    size = models.BigIntegerField(verbose_name="Dimensione file (byte)", null=True, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True, verbose_name="Data importazione")

    class Meta:
        verbose_name = "CSV importato"
        verbose_name_plural = "CSV importati"
        ordering = ['-imported_at']

    def __str__(self):
        return f"{self.path} ({self.size} bytes, mod: {self.last_modified})"

# -----------------------------------------------------------------------------#

class ColonnaImport(models.Model):
    nome = models.CharField(max_length=64, unique=True)
    description = models.TextField()
    required = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({'obbligatoria' if self.required else 'opzionale'})"

# -----------------------------------------------------------------------------#

class Sede(models.Model):
    codicesede = models.CharField(max_length=32, unique=True, verbose_name="Codice sede")
    nome = models.CharField(max_length=128, verbose_name="Nome sede")
    descrizione = models.TextField(blank=True, null=True, verbose_name="Descrizione sede")
    slug = models.SlugField(max_length=128, unique=True, blank=True)

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedi"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.codicesede} - {self.nome}"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

@receiver(pre_delete, sender=Aggregato)
def delete_aggregato_documents(sender, instance, **kwargs):
    """
    Cancella tutti i documenti associati tramite DocIndex.docs prima che l'Aggregato venga eliminato.
    Funziona anche da admin e con delete() massivo.
    """
    for docindex in instance.doc_index.all():
        docs_to_delete = list(docindex.docs.all())
        # Rimuovi la relazione M2M esplicitamente
        docindex.docs.clear()
        for doc in docs_to_delete:
            doc.delete()


