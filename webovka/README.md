# Webovka — Úloha 1

Django aplikace s databází PostgreSQL, spouštěná pomocí Docker Compose. Implementováno: založení, hledání,
čtení a úprava obchodních případů, ruční změny sedmi stavů a uložení údajů.
Vzhled vychází z klikatelného mockupu v nadřazeném adresáři.

Správa kontaktů a dokumentů, kontrola podmínek uzavření, úkoly a předávání
nejsou dosud implementované. Jejich modely jsou připravené a případné existující
záznamy se na detailu zobrazí. Výběr vlastníka je dostupný při založení;
později jej bude měnit pouze samostatná operace předání (Úloha 3).

## Spuštění

Potřebujete Docker s Docker Compose. Všechny následující příkazy spouštějte
z adresáře `webovka/`.

```sh
cp .env.example .env
chmod 600 .env
```

Pokud `.env` již existuje, nepřepisujte jej. V `.env` nastavte vlastní heslo
`POSTGRES_PASSWORD` a dlouhý náhodný `DJANGO_SECRET_KEY`. Každou hodnotu můžete
vygenerovat příkazem `openssl rand -hex 40`. Ukázkové hodnoty nejsou pro nasazení.

```sh
docker compose up --build -d --wait
docker compose logs web
```

Otevřete http://localhost:8000/. Web nejprve provede migrace a potom spustí
Gunicorn. Pokud migrace selžou, server se nespustí; důvod uvidíte v logu.
Migrace vytvoří také tři fiktivní osoby. PostgreSQL běží pouze ve vnitřní síti;
`POSTGRES_HOST=db` je jméno databázové služby, nikoli localhost.

```sh
docker compose down
docker compose up -d --wait
```

`down` odstraní kontejnery, ale pojmenovaný volume `postgres_data` zachová.
**`docker compose down -v` smaže také databázi.** Volume nenahrazuje zálohy.
Při změně názvu Compose projektu vzniká jiný volume; používejte stejný název
projektu nebo stejný adresář. Změna hesla v `.env` nezmění heslo již vytvořeného
uživatele PostgreSQL; to je nutné změnit také v databázi.
Původní `db.sqlite3` se nepoužívá a jeho data se automaticky nepřenášejí.

## K čemu slouží nové soubory

| Soubor | Účel |
| --- | --- |
| `pyproject.toml` | Určuje Python 3.14 a závislosti aplikace, nahrazuje `requirements.txt`. |
| `uv.lock` | Zamyká přesné verze závislostí pro opakovatelnou instalaci přes uv. Commituje se. |
| `Dockerfile` | Sestaví obraz, nainstaluje balíčky přes uv, připraví statické soubory a nastaví běh pod uživatelem `app`. |
| `entrypoint.sh` | Při startu provede migrace a spustí Gunicorn; `exec` předá serveru signály pro zastavení. |
| `compose.yaml` | Propojí služby `web` a `db`, počká na připravenou databázi a připojí pojmenovaný volume. |
| `.dockerignore` | Vyloučí tajné údaje, lokální databázi a virtuální prostředí z kontextu sestavení. |
| `.env.example` | Ukazuje potřebné proměnné s vymyšlenými hodnotami. Commituje se. |
| `.env` | Obsahuje skutečné místní přihlašovací údaje a konfiguraci; Git jej ignoruje. |

`config/settings.py` čte připojení z `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_HOST` a `POSTGRES_PORT`. Django klíč je povinný,
`DEBUG` je standardně vypnutý. WhiteNoise obsluhuje statické soubory i při
`DEBUG=False`; `collectstatic` se provádí při sestavení bez přístupu k databázi.
Zdrojové soubory jsou součástí obrazu, změny se projeví po novém sestavení.

## Ověření jednotlivých úkolů

1. **Závislosti:** `uv sync --locked` ověří instalaci dle lockfile
   (uv je potřeba jen pro tuto kontrolu mimo Docker).
2. **Prostředí:** `git check-ignore .env` vypíše `.env`.
   `docker compose config --quiet` zkontroluje Compose bez vypsání hesel.
3. **Obraz:** `docker compose build web` musí skončit bez chyby.
   `docker compose run --rm --no-deps web id` vypíše uživatele `app`, nikoli root.
4. **Databáze a migrace:** po `docker compose up -d --wait` zobrazí
   `docker compose ps` oba kontejnery a zdravou databázi.
   `docker compose exec web python manage.py showmigrations` zobrazí `[X]`
   u všech migrací. V prohlížeči založte případ, proveďte `down` a `up` bez `-v`
   a ověřte, že případ zůstal uložený.
5. **Aplikace a statické soubory:** otevřete hlavní stránku a
   http://localhost:8000/static/crm/app.css. Obě musí vrátit HTTP 200.
   Spusťte také:

```sh
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec web python manage.py makemigrations --check --dry-run
```

Testy používají samostatnou dočasnou databázi. Výchozí uživatel z oficiálního
obrazu PostgreSQL má právo ji vytvořit; případný omezený databázový účet
potřebuje pro testy oprávnění CREATEDB.

## Zveřejnění

Obraz je připravený pro Gunicorn a běh bez root oprávnění. Compose vystavuje
web jen na `127.0.0.1:8000`, aby se k němu připojovala HTTPS reverzní proxy
běžící na hostiteli. Databáze nemá publikovaný port. Proxy ani certifikáty
nejsou součástí těchto dvou kontejnerů.

Na serveru nastavte například:

```dotenv
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=crm.example.cz
DJANGO_CSRF_TRUSTED_ORIGINS=https://crm.example.cz
DJANGO_BEHIND_HTTPS_PROXY=True
```

Proxy musí předat původní `Host`, přepsat `X-Forwarded-Proto` podle skutečného
protokolu a zamezit přímému přístupu k Gunicornu z internetu. Teprve potom
zapněte `DJANGO_BEHIND_HTTPS_PROXY`: aktivuje HTTPS přesměrování, bezpečné cookies
a roční HSTS pro danou doménu. Pro místní HTTP jej ponechte `False`.
Po změně `.env` spusťte `docker compose up -d --force-recreate web`.

```sh
docker compose exec web python manage.py check --deploy --fail-level WARNING
```

Kontrolu spusťte se skutečným nastavením serveru. Dvě varování `security.W005`
a `security.W021` zůstávají záměrně: HSTS pro všechny subdomény a zařazení do
preload seznamu vyžadují rozhodnutí vlastníka celé domény. Proto uvedený přísný
příkaz skončí nenulovým kódem i při těchto dvou varováních. Zapínejte tato
nastavení až po ověření HTTPS na všech dotčených subdoménách. Při místním HTTP
jsou navíc očekávaná varování k HTTPS přesměrování a bezpečným cookies.
Ověřte přesměrování HTTP na HTTPS, načtení stránky a CSS přes svou doménu
a vytvoření případu přes formulář.

Aplikace zatím nemá přihlašování ani řízení přístupu: před zveřejněním CRM
s neveřejnými daty omezte přístup například autentizací na reverzní proxy.
Docker konfigurace sama přihlášení nepřidává. Zálohujte databázi a před
aktualizací proveďte zálohu; pro novou verzi použijte
`docker compose up --build -d --wait`. Hlavní verzi PostgreSQL nezvyšujte bez
plánované migrace dat.

Technické podklady: [uv v Dockeru](https://docs.astral.sh/uv/guides/integration/docker/),
[WhiteNoise](https://whitenoise.readthedocs.io/en/stable/django.html),
[oficiální obraz PostgreSQL](https://hub.docker.com/_/postgres),
[Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).

## Omezení této etapy

Správa kontaktů, dokumentů, úkolů, předávání a přihlašování zůstávají mimo
rozsah této změny. Neprobíhá automatický import údajů z HTML mockupu,
localStorage ani původní SQLite databáze.
