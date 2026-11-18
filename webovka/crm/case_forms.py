from django import forms

from .models import Case, Person


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['title', 'company', 'owner', 'stage', 'requirements', 'budget',
                  'delivery', 'questions', 'notes', 'closure_reason']
        widgets = {name: forms.Textarea(attrs={'rows': 4})
                   for name in ['requirements', 'questions', 'notes', 'closure_reason']}
        help_texts = {
            'budget': 'Například 100–150 tisíc Kč. Nezjištěný údaj nechte prázdný.',
            'delivery': 'Například únor 2027. Nezjištěný údaj nechte prázdný.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Změna vlastníka patří pouze atomickému předání v Úloze 3.
            self.fields.pop('owner')
        else:
            self.fields.pop('stage')
            self.fields['owner'].queryset = Person.objects.filter(is_active=True)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'field-input'
            field.widget.attrs['aria-describedby'] = f'id_{name}_helptext'
            if field.required:
                field.error_messages['required'] = 'Vyplňte toto pole.'
