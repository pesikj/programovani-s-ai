"""Datový základ CRM; pracovní operace přibudou v dalších úlohách."""
from django.core.validators import URLValidator
from django.db import models


class Person(models.Model):
    name = models.CharField('Jméno', max_length=200)
    is_active = models.BooleanField('Aktivní', default=True)

    class Meta:
        ordering = ['name', 'pk']

    def __str__(self):
        return self.name


class Case(models.Model):
    class Stage(models.TextChoices):
        ANALYSIS = 'ANALYSIS', 'Analýza potřeb'
        PREPARATION = 'PREPARATION', 'Příprava nabídky'
        WAITING = 'WAITING', 'Čekání na odpověď'
        NEGOTIATION = 'NEGOTIATION', 'Jednání o změnách'
        WON = 'WON', 'Vyhráno'
        REJECTED = 'REJECTED', 'Odmítnuto zákazníkem'
        UNSUITABLE = 'UNSUITABLE', 'Nevhodný před nabídkou'

    title = models.CharField('Název případu', max_length=200)
    company = models.CharField('Zákazník', max_length=200)
    owner = models.ForeignKey(Person, verbose_name='Odpovědný člověk', on_delete=models.PROTECT,
                              related_name='cases')
    stage = models.CharField('Stav', max_length=20, choices=Stage.choices, default=Stage.ANALYSIS)
    requirements = models.TextField('Požadavky', blank=True)
    budget = models.CharField('Rozpočet', max_length=200, blank=True)
    delivery = models.CharField('Termín dodání', max_length=200, blank=True)
    questions = models.TextField('Otevřené otázky', blank=True)
    notes = models.TextField('Poznámky', blank=True)
    closure_reason = models.TextField('Důvod uzavření', blank=True)
    created_at = models.DateTimeField('Vytvořeno', auto_now_add=True)
    updated_at = models.DateTimeField('Upraveno', auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-pk']

    @property
    def is_closed(self):
        return self.stage in {self.Stage.WON, self.Stage.REJECTED, self.Stage.UNSUITABLE}

    def __str__(self):
        return self.title


class Contact(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField('Jméno', max_length=200)
    role = models.CharField('Role', max_length=200, blank=True)
    email = models.EmailField('E-mail', blank=True)
    phone = models.CharField('Telefon', max_length=80, blank=True)
    contact_when = models.TextField('Kdy kontaktovat', blank=True)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return self.name


class Document(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField('Název dokumentu', max_length=200)
    url = models.URLField('Odkaz', max_length=2000, validators=[URLValidator(schemes=['http', 'https'])])
    kind = models.CharField('Účel dokumentu', max_length=200, blank=True)
    is_current_offer = models.BooleanField('Aktuální nabídka', default=False)
    is_signed_offer = models.BooleanField('Podepsaná nabídka', default=False)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return self.title


class Task(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField('Úkol', max_length=200)
    owner = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='tasks')
    due_date = models.DateField('Termín')
    completed_at = models.DateTimeField('Dokončeno', blank=True, null=True)
    result = models.TextField('Výsledek', blank=True)

    class Meta:
        ordering = ['due_date', 'pk']

    def __str__(self):
        return self.title


class Handoff(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='handoffs')
    from_owner = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='handoffs_from')
    to_owner = models.ForeignKey(Person, on_delete=models.PROTECT, related_name='handoffs_to')
    created_at = models.DateTimeField('Předáno', auto_now_add=True)
    task_count = models.PositiveIntegerField('Počet převedených úkolů', default=0)

    class Meta:
        ordering = ['-created_at', '-pk']
