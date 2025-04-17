# LazyTrainer – Guida rapida a database, tabelle e migrazioni

> **Scopo**: avere in un unico posto tutti gli step e i comandi essenziali per accendere Postgres, creare/aggiornare lo schema e lavorare in locale con Jupyter o FastAPI.

---

## 1 · Prerequisiti

| Tool | Versione minima | Note |
|------|-----------------|------|
| Docker + docker‑compose | 24.x | usato solo per Postgres (service `db`) |
| Python | 3.11+ | venv attivo in VS Code |
| pgAdmin 4 | facoltativo | per ispezionare le tabelle |
| Alembic | 1.13+ | gestisce le migrazioni |

Installa i pacchetti Python con:
```bash
pip install -r requirements.txt
pip install alembic  # se non presenti
```

---

## 2 · File creati/aggiornati

```
app/
├── db_models.py   # modelli SQLAlchemy (stile Mapped 2.0)
├── db.py          # engine + SessionLocal + costruzione dinamica DATABASE_URL
└── create_tables.py  # script "una tantum" per lo schema iniziale
alembic/
└── env.py         # puntato a Base.metadata + load_dotenv + set url
```

> ⚙️ Aggiungi (o lascia invariato) un `__init__.py` vuoto in `app/` per renderlo un pacchetto importabile.

---

## 3 · Variabili d’ambiente (`.env`)

```env
POSTGRES_USER=EmanueleCeglia
POSTGRES_PASSWORD=xxxxxxxx
POSTGRES_DB=LazyTrainer_db
# opzionale: POSTGRES_HOST=localhost (default)
# non serve DATABASE_URL – viene costruito al volo da app/db.py
```

### Come funziona la costruzione dinamica
```python
# estratto da app/db.py
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "postgres")
host = os.getenv("POSTGRES_HOST", "localhost")
db = os.getenv("POSTGRES_DB", "postgres")
DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:5432/{db}"
```

---

## 4 · Accendere solo Postgres

```bash
docker compose up -d db      # lancia il servizio `db` e resta in background
docker compose ps            # verifica che sia running
```

---

## 5 · Creare lo schema iniziale

```bash
# dalla root del progetto (venv attivo)
python -m app.create_tables   # stampa "✅  Tables created!" se va a buon fine
```

Tabelle risultanti (schema `public`): `muscles`, `exercises`, `exercise_muscles` + enum `role_enum`.

---

## 6 · Popolare o testare da Jupyter

```python
from app.db import SessionLocal
from app.db_models import Muscle, Exercise

db = SessionLocal()
quad = Muscle(name="quadriceps")
squat = Exercise(name="Barbell Back Squat")
squat.muscles.append(quad)

db.add_all([quad, squat])
db.commit()
```

---

## 7 · Gestire modifiche di schema con Alembic

1. **Init** (solo la prima volta)
   ```bash
   alembic init alembic
   ```
2. **Modifica i modelli** (`db_models.py`).
3. **Genera la migration**
   ```bash
   alembic revision --autogenerate -m "descrizione"
   ```
4. **Applica** al DB corrente
   ```bash
   alembic upgrade head
   ```
5. **Rollback** (ultimo step)
   ```bash
   alembic downgrade -1
   ```

> Alembic usa `load_dotenv()` + le env per impostare `sqlalchemy.url` in `alembic/env.py`. Nessun duplicato di credenziali.

---

## 8 · Comandi rapidi (che userai spesso)

```bash
# Avvia / Ferma Postgres
 docker compose up -d db
 docker compose stop db

# Creazione schema (una sola volta)
 python -m app.create_tables

# Loop tipico sviluppo
 # 1) modifica modelli
 alembic revision --autogenerate -m "feat: nuova colonna"
 # 2) applica
 alembic upgrade head

# Verifica stato migrazioni
 alembic current     # versione attuale
 alembic history     # lista di tutte le revision
```

---

## 9 · Debug & Tips

* **Errore `NoSuchModuleError: driver`** → imposta correttamente l’URL in `alembic/env.py` (vedi §3).
* **IDE segnala `config` indefinito** → inserisci `config.set_main_option()` dopo `config = context.config`.
* **pgAdmin non vede le nuove tabelle** → click destro su *Tables > Refresh* o riapri il nodo `public`.
* **Testing isolato** → avvia un container Postgres temporaneo o usa un DB in‑memory e sovrascrivi `POSTGRES_DB`.

---

### Done

Con questa guida puoi:
- avviare il DB in un comando,
- creare/aggiornare lo schema senza perdere dati,
- sperimentare da Jupyter o via API,
- tenere traccia delle evoluzioni nel tempo.

Buon sviluppo con *LazyTrainer*! 🚀
