# Deploying Groovelog

One server runs everything: Caddy (HTTPS + static frontend + `/api` proxy), Gunicorn, and Postgres, via `docker-compose.prod.yml`. Only Caddy is reachable from the internet.

## 1. Create the server (Hetzner Cloud)

- **Image:** Ubuntu 24.04
- **Type:** CX22 (2 vCPU, 4 GB). CX types are EU-only; for a US location pick the CPX equivalent with 4 GB.
- **Networking:** keep public IPv4 on.
- **SSH key:** add yours (`ssh-keygen -t ed25519` if you don't have one; paste `~/.ssh/id_ed25519.pub`).
- **Firewall:** allow inbound TCP 22, 80, 443 and UDP 443.

Note the server's IPv4 address, e.g. `203.0.113.7`. Without your own domain, the site's hostname is that IP with dashes plus `.sslip.io`: `203-0-113-7.sslip.io`.

## 2. Install Docker and get the code

```sh
ssh root@203.0.113.7
curl -fsSL https://get.docker.com | sh
git clone https://github.com/aaranya1/music-review-webapp.git groovelog
cd groovelog
```

## 3. Configure

```sh
cp .env.prod.example .env.prod
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 24)/" .env.prod
sed -i "s/^JWT_ACCESS_KEY=.*/JWT_ACCESS_KEY=$(openssl rand -hex 32)/" .env.prod
sed -i "s/^JWT_REFRESH_KEY=.*/JWT_REFRESH_KEY=$(openssl rand -hex 32)/" .env.prod
nano .env.prod   # set DOMAIN, e.g. 203-0-113-7.sslip.io
```

## 4. Load the music catalog

On **your machine** (Git Bash, with the local DB container running), export the catalog without user data:

```sh
X=""; for t in user review review_like review_comment comment_like backlog follow list list_item notification; do X="$X --exclude-table-data=public.$t"; done
docker exec jukeboxed-db pg_dump -U jukeboxed -d jukeboxed --no-owner --no-privileges $X > catalog.sql
scp catalog.sql root@203.0.113.7:groovelog/
```

On **the server**, start only the database, restore, then start everything:

```sh
alias prod='docker compose -f docker-compose.prod.yml --env-file .env.prod'
prod up -d db
prod exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1' < catalog.sql
prod up -d --build
```

Restore **before** the first full `up`: the API runs migrations on start, and the dump already contains the schema.

## 5. Check it

```sh
curl https://203-0-113-7.sslip.io/api/health/ready   # {"status":"ready"}
prod ps                                              # all three "Up"
prod logs -f web                                      # certificate issuance, requests
```

The first request can take a few seconds while Caddy obtains the certificate.

## Day to day

| Task | Command (on the server, in `~/groovelog`) |
|---|---|
| Deploy new code | `git pull && prod up -d --build` |
| Logs | `prod logs -f api` (or `web`, `db`) |
| Restart | `prod restart api` |
| Stop | `prod down` (data is kept in Docker volumes) |

**Backups** — nightly dump, keeping a week:

```sh
mkdir -p ~/backups && crontab -e
# add:
0 4 * * * cd ~/groovelog && docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' | gzip > ~/backups/groovelog-$(date +\%F).sql.gz && find ~/backups -name '*.sql.gz' -mtime +7 -delete
```

Copy one off the server now and then: `scp root@203.0.113.7:backups/*.sql.gz .`

**Catalog updates later:** don't re-run step 4 on a live server. Restoring a full dump would replace user accounts and reviews.

## Shutting it down

Hetzner bills hourly until the server is **deleted**; a powered-off server is still billed. Take a final backup first if you want the data:

```sh
prod exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > final.sql
```

then delete the server in the Hetzner console.
