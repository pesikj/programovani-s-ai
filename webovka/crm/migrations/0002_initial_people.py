from django.db import migrations


def add_people(apps, schema_editor):
    Person = apps.get_model('crm', 'Person')
    for name in ('Jana Nováková', 'Pavel Svoboda', 'Eva Malá'):
        Person.objects.using(schema_editor.connection.alias).get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [('crm', '0001_initial')]
    # Zpětná migrace osoby nemaže; mohly již získat případy či historii.
    operations = [migrations.RunPython(add_people, migrations.RunPython.noop)]
