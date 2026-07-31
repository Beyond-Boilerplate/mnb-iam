# Local Setup — SailPoint IdentityIQ 8.5

This guide walks you through standing up a **local IdentityIQ 8.5** lab. **Two supported paths** (pick one):

| Path | Best for | Start here |
| --- | --- | --- |
| **A. Docker** (Postgres + GHCR/local IIQ image) | Container-first; closer to homelab | [`tools/lab/docker/README.md`](../tools/lab/docker/README.md) |
| **B. Tomcat + MySQL** (host install) | Native macOS/Linux/Windows lab | Sections below / `./tools/lab/up.sh` |

Both use the same curriculum, `lab-data/`, and lesson verifier ([LESSON_VERIFY.md](LESSON_VERIFY.md)). Homelab CD remains the shared site option.

### Path A — Docker (IIQ + Academy + MCP + OpenAPI, one command)

```bash
./tools/lab/docker/up.sh
# Academy: http://localhost:4173/   (lessons + Verify now)
# IIQ:     http://localhost:8080/identityiq  (spadmin / admin)
# OpenAPI: http://localhost:8765/swagger/
# MCP:     http://127.0.0.1:8766/mcp  (Bearer mnb-lab-mcp-key)
# Teller:  http://localhost:4180/  (chatbot; OPENROUTER_API_KEY for free-text)
```

See [`tools/lab/docker/README.md`](../tools/lab/docker/README.md).

### Path B — Tomcat + MySQL (one command)

```bash
./tools/lab/up.sh
# Academy: http://localhost:4173/   (lessons + Verify now)
# IIQ:     http://localhost:8080/identityiq  (spadmin / admin)
# OpenAPI: http://localhost:8765/swagger/
# MCP:     http://127.0.0.1:8766/mcp
# Teller:  http://localhost:4180/
```

First run installs JDK/MySQL/Tomcat + init; later runs start MySQL/Tomcat if needed, then Academy.
Preflight: `./tools/lab/up.sh --check`. Install-only (no Academy): `./tools/lab/setup-local.sh`.

```bash
# Day-2 customization builds (SSD/SSB) — separate from lab up
export SPTARGET=sandbox
./build.sh clean war
```

```powershell
# Windows native
.\tools\lab\setup-local.ps1 -Check
.\tools\lab\setup-local.ps1
. $PROFILE
```

Tear down lab runtime:

```bash
./tools/lab/teardown-local.sh --yes          # Tomcat path
./tools/lab/docker/down.sh -v                # Docker path (+ wipe DB volume)
```

See [SSD.md](SSD.md) for build/CI, [../tools/lab/README.md](../tools/lab/README.md) for Tomcat bootstrap, and [LESSON_VERIFY.md](LESSON_VERIFY.md) for pass/fail checks. The rest of this document is the **manual Tomcat** walkthrough.

Official deep docs also live in `identityiq-8.5/doc/` (especially `8.5_IdentityIQ_Installation_Guide.pdf`).

---

## What you are installing

| Piece | Role |
| --- | --- |
| **JDK** | Runs Tomcat and the `iiq` console |
| **Apache Tomcat** | Application server that hosts `identityiq.war` |
| **MySQL** | IdentityIQ databases (`identityiq`, `identityiqah`, `identityiqPlugin`) |
| **IdentityIQ 8.5** | The product in `identityiq-8.5/` |

Default UI login after a successful install:

- **URL:** `http://localhost:8080/identityiq`
- **User:** `spadmin`
- **Password:** `admin`

---

## Step 0 — Confirm this repo has the bits

You should see:

```text
Sailpoint/
├── identityiq-8.5/
│   ├── identityiq.war          ← the application
│   ├── database/               ← SQL create/upgrade scripts
│   ├── doc/                    ← official PDFs
│   ├── integration/            ← optional connectors / add-ons
│   └── ConnectorGateway-*.zip  ← optional
├── lab-data/                   ← Meridian HR, apps, SoD, JML scenario files
├── docs/lessons/               ← IdentityIQ curriculum (Markdown)
├── learn/                      ← static site builder for sailpoint.lmsapp.us
├── docker-compose.iiq.yml      ← optional Docker local IIQ
└── tools/iiq-verify/           ← lesson pass/fail verifier
```

If `identityiq.war` is missing **and** you are not using the Docker GHCR image path, stop and obtain the IdentityIQ 8.5 distribution again.

---

## Step 1 — Install prerequisites

### 1.1 Java (JDK 11 or 17 recommended)

```bash
java -version
```

You want a supported JDK (11 or 17). Temurin / Oracle / Amazon Corretto are all fine for a lab.

If Java is missing (macOS Homebrew example):

```bash
brew install temurin17
```

### 1.2 Apache Tomcat 9.x

Download Tomcat 9 from [https://tomcat.apache.org/](https://tomcat.apache.org/) and unpack it somewhere convenient, for example:

```text
~/apps/apache-tomcat-9.x.x
```

Set an env var (add to `~/.zshrc` if you want it permanent):

```bash
export CATALINA_HOME=~/apps/apache-tomcat-9.x.x
export PATH="$CATALINA_HOME/bin:$PATH"
```

Raise Tomcat memory for IdentityIQ. Create or edit `$CATALINA_HOME/bin/setenv.sh`:

```bash
#!/bin/sh
export JAVA_OPTS="-Xms1024m -Xmx2048m -Djava.awt.headless=true"
```

```bash
chmod +x "$CATALINA_HOME/bin/setenv.sh"
```

> **Tip:** On a laptop with 16 GB RAM, `-Xmx2048m` is a good starting point. Increase if aggregations or certifications feel slow.

### 1.3 MySQL 8.x

Install and start MySQL (Homebrew example):

```bash
brew install mysql
brew services start mysql
mysql -u root -p -e "SELECT VERSION();"
```

Confirm you can log in as root. You will need that for Step 2.

---

## Step 2 — Create the IdentityIQ databases

IdentityIQ needs **three** schemas (names must match `iiq.properties`):

| Database | Default user | Default password |
| --- | --- | --- |
| `identityiq` | `identityiq` | `identityiq` |
| `identityiqah` | `identityiqah` | `identityiqah` |
| `identityiqPlugin` | `identityiqPlugin` | `identityiqPlugin` |

From the repo root:

```bash
cd identityiq-8.5/database
mysql -u root -p < create_identityiq_tables-8.5.mysql
```

Verify:

```bash
mysql -u root -p -e "SHOW DATABASES LIKE 'identityiq%';"
```

You should see `identityiq`, `identityiqah`, and `identityiqPlugin`.

> **Windows / other DBs:** Matching scripts exist for Oracle, PostgreSQL, and SQL Server in the same folder (`create_identityiq_tables-8.5.*`).

---

## Step 3 — Deploy the WAR into Tomcat

Do **not** drop the `.war` file into `webapps` and hope for the best on a first lab install. Unpack it into a fixed folder named `identityiq`.

```bash
export IIQ_HOME="$CATALINA_HOME/webapps/identityiq"
mkdir -p "$IIQ_HOME"
cd "$IIQ_HOME"
jar xf /path/to/Sailpoint/identityiq-8.5/identityiq.war
```

Replace `/path/to/Sailpoint` with your real workspace path, for example:

```bash
jar xf /Users/alishaghatane/Documents/Sailpoint/identityiq-8.5/identityiq.war
```

Confirm these exist:

```bash
ls "$IIQ_HOME/WEB-INF/classes/iiq.properties"
ls "$IIQ_HOME/WEB-INF/bin/iiq"
ls "$IIQ_HOME/WEB-INF/config/init.xml"
```

Make the console script executable:

```bash
chmod +x "$IIQ_HOME/WEB-INF/bin/iiq"
```

---

## Step 4 — Configure `iiq.properties`

Edit:

```text
$IIQ_HOME/WEB-INF/classes/iiq.properties
```

For a **local MySQL lab**, the shipping defaults are already MySQL-oriented:

- `dataSource.url` → `jdbc:mysql://localhost/identityiq?...`
- `dataSource.username` → `identityiq`
- `pluginsDataSource.*` → `identityiqPlugin`
- `dataSourceAccessHistory.*` → `identityiqah`

### 4.1 Set database passwords (important)

The shipped `iiq.properties` contains **encrypted** password values that may not match your DB users. For a local lab you have two options.

**Option A — plaintext for lab only (fastest)**

Temporarily set:

```properties
dataSource.password=identityiq
pluginsDataSource.password=identityiqPlugin
dataSourceAccessHistory.password=identityiqah
```

**Option B — encrypt with `iiq` console (better habit)**

After Step 5’s classpath works, from `$IIQ_HOME/WEB-INF/bin`:

```bash
./iiq encrypt identityiq
./iiq encrypt identityiqPlugin
./iiq encrypt identityiqah
```

Paste each encrypted value into the matching password property.

Also confirm **exactly one** Hibernate dialect is uncommented for MySQL:

```properties
sessionFactory.hibernateProperties.hibernate.dialect=org.hibernate.dialect.MySQL57Dialect
```

---

## Step 5 — Import the base configuration (`init.xml`)

Tomcat should be **stopped** for this step.

```bash
"$CATALINA_HOME/bin/shutdown.sh" 2>/dev/null || true
```

Run the IdentityIQ console from the deployed app:

```bash
cd "$IIQ_HOME/WEB-INF/bin"
./iiq console
```

At the `>` prompt:

```text
import init.xml
```

Wait until it finishes without errors, then:

```text
quit
```

### Optional — activate Lifecycle Manager objects

If you will practice joiners / movers / leavers and access requests (recommended for the lessons):

```bash
./iiq console
```

```text
import init-lcm.xml
quit
```

Also review `identityiq-8.5/doc/8.5_Lifecycle_Manager_Activation.pdf` for license / feature activation notes in non-lab environments.

---

## Step 6 — Start Tomcat and open IdentityIQ

```bash
"$CATALINA_HOME/bin/startup.sh"
tail -f "$CATALINA_HOME/logs/catalina.out"
```

Wait until the log shows the application started (no stack traces about DB connectivity).

Open:

```text
http://localhost:8080/identityiq
```

Log in:

| Field | Value |
| --- | --- |
| Username | `spadmin` |
| Password | `admin` |

Change the `spadmin` password after first login if this machine is shared.

---

## Step 7 — Smoke-check the lab

Do these quickly before diving into lessons:

1. **Home page loads** and you see the IdentityIQ menu.
2. **Debug → About** (or gear / gear-adjacent admin areas) shows version **8.5**.
3. **Setup → Applications** opens (empty is fine).
4. Copy sample data into a stable lab folder (used by later lessons):

```bash
mkdir -p ~/iiq-lab-data
cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/
cp -R lab-data/apps lab-data/scenarios lab-data/reference lab-data/notifications lab-data/connectors ~/iiq-lab-data/
```

---

## Step 8 — Day-2 operations cheat sheet

| Task | Command / action |
| --- | --- |
| Start | `$CATALINA_HOME/bin/startup.sh` |
| Stop | `$CATALINA_HOME/bin/shutdown.sh` |
| Logs | `tail -f $CATALINA_HOME/logs/catalina.out` |
| Console | `cd $IIQ_HOME/WEB-INF/bin && ./iiq console` |
| Encrypt secret | `./iiq encrypt 'mySecret'` |
| Re-import object XML | `import path/to/file.xml` inside console |

---

## Troubleshooting (common first-time failures)

### Tomcat starts but `/identityiq` is 404

- Confirm the app is deployed under `$CATALINA_HOME/webapps/identityiq` (folder), not only as an unexploded `.war`.
- Confirm Tomcat HTTP port is really `8080` (`$CATALINA_HOME/conf/server.xml`).

### Login page never loads / DB errors in logs

- MySQL running?
- Databases created?
- `iiq.properties` usernames/passwords/URLs correct?
- MySQL 8 auth plugin issues: the create script uses `mysql_native_password` for lab users — re-run the user statements if you created users manually another way.

### `./iiq console` fails immediately

- `java -version` works in the same shell.
- You are inside the **deployed** `$IIQ_HOME/WEB-INF/bin`, not the raw distribution folder (the distribution has no exploded WEB-INF until you unpack the WAR).
- `chmod +x iiq` was run.

### Import fails halfway

- Drop and recreate databases (lab only!), then re-import `init.xml`:

```bash
mysql -u root -p < identityiq-8.5/database/drop_identityiq_tables-8.5.mysql
mysql -u root -p < identityiq-8.5/database/create_identityiq_tables-8.5.mysql
```

Then repeat Step 5.

### OutOfMemoryError

Increase `-Xmx` in `setenv.sh` and restart Tomcat.

---

## Suggested next reading

1. [INFRASTRUCTURE.md](INFRASTRUCTURE.md) — how the stack fits together  
2. [lessons/README.md](lessons/README.md) — Meridian National Bank 50-lesson path  
3. [LEARN-SITE.md](LEARN-SITE.md) — publish lessons at iam.lmsapp.us/learn  
4. `identityiq-8.5/doc/8.5_IdentityIQ_Getting_Started.pdf`  
5. `identityiq-8.5/doc/8.5_IdentityIQ_Installation_Guide.pdf`

---

## Quick sequential checklist

- [ ] JDK 11/17 installed (`java -version`)
- [ ] Tomcat 9 installed; `CATALINA_HOME` set; heap configured
- [ ] MySQL 8 running
- [ ] Ran `create_identityiq_tables-8.5.mysql`
- [ ] Exploded `identityiq.war` into `$CATALINA_HOME/webapps/identityiq`
- [ ] Edited `iiq.properties` passwords/URLs
- [ ] Imported `init.xml` (and optionally `init-lcm.xml`) via `iiq console`
- [ ] Started Tomcat; logged in as `spadmin` / `admin`
- [ ] Copied Meridian `lab-data/` files to `~/iiq-lab-data`
