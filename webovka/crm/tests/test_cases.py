"""Testy uživatelských operací Úlohy 1; žádné síťové služby."""
from datetime import date

from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from crm.models import Case, Contact, Document, Handoff, Person, Task


class CaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = Person.objects.create(name='Testovací Jana')
        cls.other = Person.objects.create(name='Testovací Pavel')
        cls.inactive = Person.objects.create(name='Neaktivní Eva', is_active=False)

    def payload(self, **changes):
        return {'title': 'Modernizace webu', 'company': 'Alfa studio s.r.o.',
                'owner': self.owner.pk, 'stage': 'ANALYSIS', **changes}

    def make_case(self, **changes):
        return Case.objects.create(title='Modernizace webu', company='Alfa studio s.r.o.',
                                   owner=self.owner, **changes)

    def test_create_minimal_case_and_reopen(self):
        response = self.client.post(reverse('crm:case-create'), {
            'title': 'Modernizace webu', 'company': 'Alfa studio s.r.o.', 'owner': self.owner.pk,
        })
        case = Case.objects.get(title='Modernizace webu')
        self.assertEqual(case.stage, 'ANALYSIS')
        self.assertEqual(case.owner, self.owner)
        self.assertFalse(case.tasks.exists())
        self.assertRedirects(response, reverse('crm:case-detail', args=[case.pk]))
        response = Client().get(reverse('crm:case-detail', args=[case.pk]))
        self.assertContains(response, 'Modernizace webu')
        self.assertContains(response, 'Bez dalšího kroku')
        self.assertContains(response, 'Nezjištěno')

    def test_offer_deadline_can_be_created_edited_and_cleared(self):
        response = self.client.post(reverse('crm:case-create'),
                                    self.payload(offer_deadline='2027-02-15'))
        case = Case.objects.get()
        self.assertRedirects(response, reverse('crm:case-detail', args=[case.pk]))
        self.assertEqual(case.offer_deadline, date(2027, 2, 15))
        response = self.client.get(reverse('crm:case-detail', args=[case.pk]))
        self.assertContains(response, 'Termín odeslání nabídky')
        self.assertContains(response, '15. 2. 2027')
        response = self.client.get(reverse('crm:case-update', args=[case.pk]))
        self.assertContains(response, 'type="date"')
        self.assertContains(response, 'value="2027-02-15"')
        self.client.post(reverse('crm:case-update', args=[case.pk]),
                         self.payload(offer_deadline='2027-03-01'))
        case.refresh_from_db()
        self.assertEqual(case.offer_deadline, date(2027, 3, 1))
        response = self.client.post(reverse('crm:case-update', args=[case.pk]),
                                    self.payload(offer_deadline='2027-02-30'))
        self.assertIn('offer_deadline', response.context['form'].errors)
        case.refresh_from_db()
        self.assertEqual(case.offer_deadline, date(2027, 3, 1))
        self.client.post(reverse('crm:case-update', args=[case.pk]),
                         self.payload(offer_deadline=''))
        case.refresh_from_db()
        self.assertIsNone(case.offer_deadline)

    def test_blank_case_is_rejected(self):
        for changes in ({'title': '   '}, {'company': '   '}, {'owner': ''},
                        {'owner': self.inactive.pk}):
            with self.subTest(changes=changes):
                response = self.client.post(reverse('crm:case-create'), self.payload(**changes))
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context['form'].errors)
                self.assertEqual(Case.objects.count(), 0)

    def test_search_and_empty_results(self):
        case = self.make_case()
        for query in ('modernizace', 'Alfa', '  Alfa  '):
            with self.subTest(query=query):
                response = self.client.get(reverse('crm:case-list'), {'q': query})
                self.assertContains(response, reverse('crm:case-detail', args=[case.pk]))
        response = self.client.get(reverse('crm:case-list'), {'q': 'Neexistující firma'})
        self.assertNotContains(response, case.title)
        self.assertContains(response, 'Žádný odpovídající případ')

    def test_filter_by_stage_and_show_all_stages(self):
        cases = [self.make_case(stage=stage) for stage in Case.Stage.values]
        for stage, label in Case.Stage.choices:
            with self.subTest(stage=stage):
                response = self.client.get(reverse('crm:case-list'), {'stage': stage})
                self.assertEqual(list(response.context['cases']),
                                 [case for case in cases if case.stage == stage])
                self.assertContains(response, f'<option value="{stage}" selected>{label}</option>',
                                    html=True)
        for params in ({}, {'stage': ''}):
            response = self.client.get(reverse('crm:case-list'), params)
            self.assertCountEqual(response.context['cases'], cases)
            self.assertContains(response, '<option value="" selected>Všechny stavy</option>',
                                html=True)
            for stage, label in Case.Stage.choices:
                self.assertContains(response, f'<option value="{stage}">{label}</option>',
                                    html=True)

    def test_stage_filter_combines_with_search_and_preserves_values(self):
        matching = self.make_case(stage=Case.Stage.WON)
        self.make_case(stage=Case.Stage.ANALYSIS)
        Case.objects.create(title='Jiný případ', company='Beta', owner=self.owner,
                            stage=Case.Stage.WON)
        for query in ('Modernizace', 'Alfa'):
            with self.subTest(query=query):
                response = self.client.get(reverse('crm:case-list'),
                                           {'q': query, 'stage': Case.Stage.WON})
                self.assertEqual(list(response.context['cases']), [matching])
                self.assertContains(response, f'value="{query}"')
                self.assertContains(response, '<option value="WON" selected>Vyhráno</option>',
                                    html=True)
        response = self.client.get(reverse('crm:case-list'), {'stage': Case.Stage.REJECTED})
        self.assertContains(response, 'Žádný odpovídající případ')
        self.assertNotContains(response, 'Zatím tu není žádný případ')

    def test_update_notes_and_reopen_closed_case(self):
        case = self.make_case(stage='REJECTED', closure_reason='Vybrali konkurenci.')
        history = Handoff.objects.create(case=case, from_owner=self.other,
                                         to_owner=self.owner, task_count=0)
        response = self.client.post(reverse('crm:case-update', args=[case.pk]),
                                    self.payload(notes='Zákazník obnovil jednání.',
                                                 owner=self.other.pk))
        self.assertRedirects(response, reverse('crm:case-detail', args=[case.pk]))
        case.refresh_from_db()
        self.assertEqual(case.stage, 'ANALYSIS')
        self.assertEqual(case.notes, 'Zákazník obnovil jednání.')
        self.assertEqual(case.owner, self.owner)  # editace nesmí obejít budoucí předání
        self.assertTrue(Handoff.objects.filter(pk=history.pk).exists())

    def test_all_stages_can_be_changed_manually_in_task_one(self):
        case = self.make_case()
        for stage in ('ANALYSIS', 'PREPARATION', 'WAITING', 'NEGOTIATION',
                      'WON', 'REJECTED', 'UNSUITABLE'):
            with self.subTest(stage=stage):
                self.client.post(reverse('crm:case-update', args=[case.pk]),
                                 self.payload(stage=stage, closure_reason='Ruční zkouška.'))
                case.refresh_from_db()
                self.assertEqual(case.stage, stage)
        response = self.client.post(reverse('crm:case-update', args=[case.pk]),
                                    self.payload(stage='NEZNAMY_STAV'))
        self.assertTrue(response.context['form'].errors)
        case.refresh_from_db()
        self.assertEqual(case.stage, 'UNSUITABLE')

    def test_detail_displays_related_data_and_escapes_notes(self):
        case = self.make_case(notes='<script>alert(1)</script>', requirements='Kontaktní formulář')
        Contact.objects.create(case=case, name='Petr', role='Jednatel', email='petr@example.cz')
        Contact.objects.create(case=case, name='Eva', role='Marketing', phone='123456789')
        Document.objects.create(case=case, title='Fotografie', url='https://example.cz/foto',
                                kind='Fotografie od zákazníka')
        Task.objects.create(case=case, title='Zavolat zákazníkovi', owner=self.owner,
                            due_date=date(2026, 11, 18))
        Task.objects.create(case=case, title='Starší úkol', owner=self.other,
                            due_date=date(2026, 11, 13))
        Task.objects.create(case=case, title='Hotový úkol', owner=self.other,
                            due_date=date(2026, 11, 1), completed_at=timezone.now(), result='Odesláno.')
        response = self.client.get(reverse('crm:case-detail', args=[case.pk]))
        for content in ('Petr', 'Eva', 'Fotografie od zákazníka', 'Kontaktní formulář',
                        'Starší úkol', 'Odesláno.'):
            self.assertContains(response, content)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertEqual(response.context['next_task'].title, 'Starší úkol')

    def test_get_and_cancel_do_not_save_and_csrf_is_required(self):
        case = self.make_case()
        response = self.client.get(reverse('crm:case-update', args=[case.pk]))
        self.assertContains(response, reverse('crm:case-detail', args=[case.pk]))
        self.assertEqual(Case.objects.get(pk=case.pk).title, 'Modernizace webu')
        self.client.get(reverse('crm:case-create'))
        self.assertEqual(Case.objects.count(), 1)
        response = Client(enforce_csrf_checks=True).post(reverse('crm:case-create'), self.payload())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Case.objects.count(), 1)

    def test_owner_is_protected_and_document_kind_is_free_text(self):
        case = self.make_case()
        with self.assertRaises(ProtectedError):
            self.owner.delete()
        for kind in ('Fotografie od zákazníka', ''):
            doc = Document(case=case, title='Podklad', url='https://example.cz', kind=kind)
            doc.full_clean()
            doc.save()
            self.assertFalse(doc.is_current_offer)
            self.assertFalse(doc.is_signed_offer)

    def test_missing_case_returns_404(self):
        for name in ('crm:case-detail', 'crm:case-update'):
            self.assertEqual(self.client.get(reverse(name, args=[99999])).status_code, 404)
