# Webovka — Úloha 1

Lokální Django aplikace s databází SQLite. Implementováno: založení, hledání,
čtení a úprava obchodních případů, ruční změny sedmi stavů a uložení údajů.
Vzhled vychází z klikatelného mockupu v nadřazeném adresáři.

Správa kontaktů a dokumentů, kontrola podmínek uzavření, úkoly a předávání
nejsou dosud implementované. Jejich modely jsou připravené a případné existující
záznamy se na detailu zobrazí. Výběr vlastníka je dostupný při založení;
později jej bude měnit pouze samostatná operace předání (Úloha 3).

## Spuštění

Z adresáře projektu `webovka/`:

```sh
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Otevřete http://127.0.0.1:8000/. Pokud je prostředí již připravené a migrace
provedené, stačí poslední příkaz. Pro zastavení stiskněte Ctrl+C.

Použitý Python 3.14; řada Django 5.2 podporuje Python 3.10–3.14
([oficiální přehled](https://docs.djangoproject.com/en/5.2/faq/install/#what-python-version-can-i-use-with-django)).
Závislosti v requirements.txt mají přesné verze. Projekt je oddělený od
virtuálního prostředí i pyproject.toml v nadřazeném učebním adresáři.
Na Windows použijte `.venv\Scripts\python.exe` místo `.venv/bin/python`.

Migrace vytvoří tři fiktivní osoby (Jana Nováková, Pavel Svoboda, Eva Malá).
Založte si první vlastní anonymizovaný případ. Ukázkové případy a příkaz
seed_demo patří do Úlohy 4 a zatím neexistují. Opakované `migrate` údaje
nepřepíše. Databáze je v `db.sqlite3`; restart serveru ji nesmaže.

Pokud sandbox nepovoluje výchozí cache uv, lze před příkazy uv nastavit
`UV_CACHE_DIR=/private/tmp/webovka-uv-cache`. Instalace nového prostředí
vyžaduje síť nebo dříve dostupné balíčky v cache.

## Kontroly

```sh
.venv/bin/python manage.py test
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
```

Testy používají vlastní dočasnou databázi, nikoli vaše případy.

## Omezení této etapy

Tato konfigurace je pouze pro localhost a anonymizované učební údaje.
Přihlašování, týmový provoz a nasazení nejsou součástí Úlohy 1.
Podmínky uzavření (důvod odmítnutí a podepsaná nabídka) přibudou v Úloze 2;
meziverze nyní dovoluje ruční změny všech stavů bez těchto kontrol.
Neprobíhá automatický import údajů z HTML mockupu ani localStorage.
