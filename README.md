# Holdings Workbench — Local Launch Guide (`read.md`)

> **Where this file belongs:** the intended home for this guide is the project root
> (`read.md`, next to `rxconfig.py`). The editing tooling for this app can only write
> files under `app/`, so the canonical copy lives here at `app/read.md`. To finish the
> move on your own machine, run from the project root:
>
> ```bash
> git mv app/read.md read.md     # or: mv app/read.md read.md
> ```

This is the **launch guide** for running this existing Reflex project on your own
computer (Windows, macOS, or Linux). No prior Reflex experience is needed — follow
the steps in order and copy/paste the commands.

The app is a finance holdings dashboard: users register, sign in, and manage
portfolio holdings. **The first account that registers automatically becomes the
administrator**; every account after that is a standard user.

---

## 0. What you will end up with

- A Python virtual environment with the project's dependencies installed.
- A local PostgreSQL database for the app's users, sessions, portfolios, and holdings.
- A local `.env` file holding **your own** database connection strings.
- The app running at <http://localhost:3000>.

Total time: roughly 15–30 minutes the first time.

---

## 1. Prerequisites

Install these before you start. Open a fresh terminal after each install so new
commands are on your `PATH`.

| Tool | Version | Notes |
| --- | --- | --- |
| **Python** | 3.10 – 3.13 | Required by Reflex 0.9.8. Python 3.11 or 3.12 is the safest choice. |
| **Git** | any recent | Used to clone the project. |
| **PostgreSQL** | 14 or newer | The app stores everything in Postgres. Includes the `psql` client. |
| Node.js / Bun | — | **You do not install these.** Reflex downloads and manages its own frontend toolchain (Bun/Node) the first time you run the app. |

### Where to get them

- **Python** — <https://www.python.org/downloads/>
  - Windows: in the installer, tick **“Add python.exe to PATH”**.
  - macOS: `brew install python@3.12` also works.
  - Linux (Debian/Ubuntu): `sudo apt install python3 python3-venv python3-pip`
- **Git** — <https://git-scm.com/downloads>
- **PostgreSQL** — <https://www.postgresql.org/download/>
  - Windows: the EDB installer; keep **pgAdmin** and the **Command Line Tools** checked.
  - macOS: `brew install postgresql@16 && brew services start postgresql@16`, or <https://postgresapp.com>.
  - Linux (Debian/Ubuntu): `sudo apt install postgresql postgresql-contrib`
- **Windows extra:** if Reflex later reports `Install Failed - You are missing a DLL
  required to run bun.exe`, install the
  [Microsoft Visual C++ 2015 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=53840).

### Verify the prerequisites

```bash
python --version      # Windows may need: py --version
git --version
psql --version
```

If `python` is not found on macOS/Linux, try `python3 --version` and use `python3`
everywhere below.

---

## 2. Get the project (clone / open it)

If you have a Git URL for this project:

```bash
git clone <your-repository-url>
cd <project-folder>
```

If you already have the project as a folder or zip, extract it and `cd` into the
folder that contains `rxconfig.py`.

**Sanity check** — you should see these at the top level:

```
app/                 # application code (this guide: app/read.md, move it to ./read.md)
db_migrations/       # existing database migration scripts
assets/              # static files
requirements.txt
rxconfig.py
```

Every command from here on is run **from this folder** (the one with `rxconfig.py`).

---

## 3. Create and activate a virtual environment

A virtual environment keeps this project's packages separate from the rest of your
system.

### Create it (all platforms)

```bash
python -m venv .venv
```

(macOS/Linux: use `python3 -m venv .venv` if needed.)

### Activate it

**Windows — PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run this once, then activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Windows — Command Prompt (cmd.exe)**

```bat
.\.venv\Scripts\activate.bat
```

**macOS / Linux — bash or zsh**

```bash
source .venv/bin/activate
```

**Fish shell**

```fish
source .venv/bin/activate.fish
```

When it worked, your prompt starts with `(.venv)`.

> You must activate the virtual environment in **every new terminal** before running
> `reflex` commands.

To leave it later: `deactivate`.

---

## 4. Install the requirements

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

This installs `reflex[db]` 0.9.8, the `psycopg` PostgreSQL driver, and the `xy`
charting package. Confirm it worked:

```bash
reflex --version
```

If `reflex` is “not found”, your virtual environment is probably not active — go
back to step 3.

---

## 5. Create a local PostgreSQL database and user

You need one database and one database user. **Choose your own password** — never
reuse a real production password, and never paste a real password into a file you
commit or into a chat/issue tracker.

Throughout this guide the placeholders are:

- database name: `holdings_db`
- database user: `holdings_user`
- password: `YOUR_LOCAL_PASSWORD` ← replace with a password you invent

### Option A — `psql` on macOS / Linux

```bash
sudo -u postgres psql          # Linux
# macOS (Homebrew / Postgres.app): just  psql postgres
```

Then at the `postgres=#` prompt:

```sql
CREATE USER holdings_user WITH PASSWORD 'YOUR_LOCAL_PASSWORD';
CREATE DATABASE holdings_db OWNER holdings_user;
GRANT ALL PRIVILEGES ON DATABASE holdings_db TO holdings_user;
\q
```

### Option B — `psql` on Windows

Open **SQL Shell (psql)** from the Start menu (accept the defaults, enter the
`postgres` superuser password you chose during installation), then run the same
three SQL statements above.

### Option C — pgAdmin (graphical, any platform)

1. Open pgAdmin and connect to your local server.
2. **Login/Group Roles → Create → Login/Group Role…**
   - *General*: name `holdings_user`
   - *Definition*: your password
   - *Privileges*: enable **Can login**
3. **Databases → Create → Database…**
   - *Database*: `holdings_db`
   - *Owner*: `holdings_user`

### Verify the connection

```bash
psql -h localhost -p 5432 -U holdings_user -d holdings_db -c "SELECT 1;"
```

Enter your password when prompted. A table containing `1` means success.

> **Note the port.** The default is `5432`. If your Postgres runs on another port
> (e.g. `5433` when two versions are installed), use that number in the URLs below.

---

## 6. Configure your local `.env`

Reflex reads the database connection from environment variables. Create a file named
exactly `.env` in the project root (next to `rxconfig.py`).

**Windows PowerShell**

```powershell
New-Item -ItemType File .env
notepad .env
```

**macOS / Linux**

```bash
touch .env
```

Paste the following into `.env` and replace the placeholders with **your** values
from step 5:

```dotenv
# Local development only — these are PLACEHOLDERS, replace with your own values.
# Format: postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE

# Synchronous URL (used by migrations and rx.session())
DATABASE_URL=postgresql+psycopg://holdings_user:YOUR_LOCAL_PASSWORD@localhost:5432/holdings_db

# Reflex's primary (sync) database URL
REFLEX_DB_URL=postgresql+psycopg://holdings_user:YOUR_LOCAL_PASSWORD@localhost:5432/holdings_db

# Async URL used by rx.asession() in the app's state handlers
REFLEX_ASYNC_DB_URL=postgresql+psycopg://holdings_user:YOUR_LOCAL_PASSWORD@localhost:5432/holdings_db
```

Notes:

- All three variables point at the **same database**. `psycopg` (v3) drives both the
  sync and async engines, which is why the driver suffix is identical.
- Replace `YOUR_LOCAL_PASSWORD`, and `holdings_user` / `holdings_db` if you chose
  different names.
- Change `5432` if your Postgres uses another port.
- **Special characters in the password** must be percent-encoded in a URL: `@` →
  `%40`, `:` → `%3A`, `/` → `%2F`, `#` → `%23`. The simplest fix is to pick a
  password with only letters, digits, `-` and `_`.
- No quotes, and no spaces around the `=` sign.

### ⚠️ Never commit `.env`

`.env` contains credentials. Keep it out of version control:

```bash
echo ".env" >> .gitignore
```

Do not paste its contents into screenshots, bug reports, or chat messages. If a
secret is ever committed, change the password and rotate it.

---

## 7. Apply the existing database migrations

The schema (users, sessions, portfolios, holdings) already exists as a migration
script in `db_migrations/`. You do **not** create tables by hand, and you should
**not** run `reflex db init` or `reflex db makemigrations` — those would try to
create *new* migrations.

Run only this:

```bash
reflex db migrate
```

Expected output mentions Alembic “Running upgrade → e016133c0a3b, create_finance_schema”.

Verify the tables exist:

```bash
psql -h localhost -p 5432 -U holdings_user -d holdings_db -c "\dt"
```

You should see `app_user`, `holding`, `portfolio`, `user_session`, and
`alembic_version`.

---

## 8. Start the app

```bash
reflex run
```

The first run takes a few minutes: Reflex downloads its own Bun/Node toolchain and
compiles the frontend. Later runs are much faster.

When it is ready you will see something like:

```
App running at: http://localhost:3000
Backend running at: http://0.0.0.0:8000
```

For more detail while it starts:

```bash
reflex run --loglevel debug
```

---

## 9. Open the local URL

Go to <http://localhost:3000>.

Use `localhost` — not your machine's LAN IP, and avoid `127.0.0.1` — because the
session cookie is scoped to the origin you sign in on (see the cookie notes in
troubleshooting).

The landing page checks your session and then sends you to the sign-in page.

---

## 10. Register the first administrator

1. On the sign-in page, click **Register** (or go to <http://localhost:3000/register>).
2. Fill in:
   - **Email** — any valid address format, e.g. `admin@example.com`
   - **Display name** — 2–120 characters
   - **Password** — at least **10 characters**, with at least one **lowercase
     letter**, one **uppercase letter**, and one **digit**
   - **Confirm password** — must match
3. Submit.

Because this is the very first account in the database, it is granted the
**administrator** role automatically and you land on the admin dashboard at
`/admin`. Passwords are stored only as salted PBKDF2 hashes — the app never shows or
stores plaintext passwords.

### Normal behaviour for subsequent users

Every account registered after the first is a **standard user**. Sign out (button in
the header) and register a second account to see the difference:

- Standard users land on `/dashboard`, where they manage only their **own** holdings
  (add, edit, delete, search, filter, and view allocation/performance charts).
- The administrator can additionally open `/admin` to see user and portfolio
  summaries, search users, inspect and edit holdings across all accounts, change
  roles between standard/admin, and view aggregate asset and portfolio values.
- If a standard user tries to open `/admin`, they are redirected back to
  `/dashboard`.

An administrator can promote another account from the admin dashboard's user panel.

---

## 11. Stopping and restarting

**Stop:** press `Ctrl + C` in the terminal running `reflex run` (press it twice if it
doesn't exit immediately).

**Restart later** — from the project folder:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
reflex run

# macOS / Linux
source .venv/bin/activate
reflex run
```

You only need steps 5–7 (database, `.env`, migrate) once — unless you delete the
database, or the project gains a new migration, in which case run `reflex db migrate`
again after `git pull`.

Your data persists in PostgreSQL between restarts. Make sure the PostgreSQL service
is running before you start the app:

- Windows: **Services** → `postgresql-x64-16` → Start
- macOS: `brew services start postgresql@16`
- Linux: `sudo systemctl start postgresql`

---

## 12. Troubleshooting

### Database

**`connection refused` / `could not connect to server`**
PostgreSQL isn't running, or the port is wrong. Start the service (above) and confirm
with `psql -h localhost -p 5432 -U holdings_user -d holdings_db`.

**`password authentication failed for user "holdings_user"`**
The password in `.env` doesn't match the database user. Reset it:

```sql
ALTER USER holdings_user WITH PASSWORD 'YOUR_LOCAL_PASSWORD';
```

Then update all three URLs in `.env`. Remember to percent-encode special characters.

**`database "holdings_db" does not exist`**
Re-do step 5, or fix the database name at the end of the URLs.

**`relation "app_user" does not exist`**
Migrations were not applied. Run `reflex db migrate`.

**`ModuleNotFoundError: No module named 'psycopg'`**
Requirements weren't installed into the active environment. Activate `.venv`, then
`pip install -r requirements.txt`.

**`Can't load plugin: sqlalchemy.dialects:postgres`**
Your URL starts with `postgres://`. Use `postgresql+psycopg://` as in step 6.

**`permission denied for schema public` (PostgreSQL 15+)**
Connected to `holdings_db` as a superuser:

```sql
GRANT ALL ON SCHEMA public TO holdings_user;
ALTER SCHEMA public OWNER TO holdings_user;
```

**Start completely over (destroys all app data):**

```sql
DROP DATABASE holdings_db;
CREATE DATABASE holdings_db OWNER holdings_user;
```

Then run `reflex db migrate` again.

### Ports

**`Address already in use` on 3000 or 8000**
Something else is using the port. Either stop it, or run Reflex elsewhere:

```bash
reflex run --frontend-port 3001 --backend-port 8001
```

Then open <http://localhost:3001>.

Find the offender:

```powershell
# Windows
netstat -ano | findstr :3000
taskkill /PID <pid> /F
```

```bash
# macOS / Linux
lsof -i :3000
kill -9 <pid>
```

A previous `reflex run` that didn't shut down cleanly is the usual cause — closing
the old terminal fixes it.

### Sign-in, cookies, and “secure” on localhost

The session cookie (`fw_session`) is marked **Secure**, which browsers normally only
send over HTTPS. Modern browsers treat `http://localhost` as a trusted secure
context, so signing in there works without any HTTPS setup.

**Symptom: you register or sign in successfully but are bounced straight back to
`/login`.** The cookie isn't returning to the server. Try, in order:

1. Use exactly `http://localhost:3000` — **not** `http://127.0.0.1:3000` and not a
   LAN IP such as `http://192.168.x.x:3000`. Those origins aren't always treated as
   secure contexts, so a `Secure` cookie can be dropped.
2. Use a normal window, not a private/incognito window with all cookies blocked.
3. Check the browser isn't set to “block all cookies”
   (Chrome/Edge: `Settings → Privacy → Cookies`; Safari: temporarily uncheck
   *Prevent cross-site tracking*).
4. Clear cookies for `localhost` and sign in again: DevTools →
   **Application → Storage → Cookies → http://localhost:3000 → Clear**.
5. After signing in, confirm `fw_session` is listed under
   DevTools → **Application → Cookies**.
6. Restart the browser after changing cookie settings.

**Accessing the app from another device on your network** isn't covered here: a
`Secure` cookie over plain HTTP to a LAN IP will be rejected, so you would need
HTTPS. Stick to `localhost` for local development.

**Forgot the admin password?** There is no password-reset flow. Either register a new
account and have an existing admin promote it, or delete the account row and register
again:

```sql
DELETE FROM app_user WHERE email = 'admin@example.com';
```

(That also removes that user's portfolio, holdings, and sessions.)

### Other

**Blank page or stale UI after code changes** — stop the app, delete the generated
frontend, rerun:

```bash
rm -rf .web        # Windows PowerShell: Remove-Item -Recurse -Force .web
reflex run
```

**First run stuck on “Installing frontend packages”** — this downloads Bun/Node and
can take several minutes on a slow connection. Let it finish; if it fails, rerun with
`reflex run --loglevel debug`.

**Windows: `bun.exe` DLL error** — install the
[Microsoft Visual C++ 2015 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=53840).

---

## 13. Command checklist

Copy/paste version, run from the project root.

**Windows (PowerShell)**

```powershell
git clone <your-repository-url>
cd <project-folder>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
# create holdings_db + holdings_user in psql or pgAdmin        (step 5)
# create .env with DATABASE_URL / REFLEX_DB_URL / REFLEX_ASYNC_DB_URL  (step 6)
echo ".env" >> .gitignore
reflex db migrate
reflex run
# open http://localhost:3000 and register the first (admin) account
```

**macOS / Linux**

```bash
git clone <your-repository-url>
cd <project-folder>
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
psql postgres -c "CREATE USER holdings_user WITH PASSWORD 'YOUR_LOCAL_PASSWORD';"
psql postgres -c "CREATE DATABASE holdings_db OWNER holdings_user;"
# create .env with DATABASE_URL / REFLEX_DB_URL / REFLEX_ASYNC_DB_URL  (step 6)
echo ".env" >> .gitignore
reflex db migrate
reflex run
# open http://localhost:3000 and register the first (admin) account
```

**Every day after that**

```bash
source .venv/bin/activate      # or .\.venv\Scripts\Activate.ps1
reflex run
```

---

**Reminder:** `.env` holds your database password. Keep it local, keep it out of Git,
and use placeholder values (like `YOUR_LOCAL_PASSWORD`) whenever you share these
instructions with someone else.
