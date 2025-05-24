# certbot-nginx-manager

A simple CLI utility for managing Nginx and Certbot certificates. The script uses **your configuration** to create ready-to-use HTTPS sites with a single command and can also renew certificates manually when needed.

## Features

- 🔒 Automatically renew expiring SSL certificates via `cron`
- ⚙️ Create and configure new HTTPS domains with your predefined Nginx/Cerbot settings
- 🛠 Manually update certificates for specific domains when desired
- 🧩 Uses a JSON config file to store paths, email, base domain and renewal policy

## Requirements

- Python 3.10+
- `certbot` with nginx plugin installed
- `nginx` running with `sites-enabled` structure

## Installation

```bash
git clone https://github.com/yourusername/certbot-nginx-manager.git
cd certbot-nginx-manager
````

## Configuration

Create a `config.json` file in the project root:

```json
{
  "domain": "yourdomain.com",
  "email": "your@email.com",
  "cron_days": 2,
  "paths": {
    "nginx": "/etc/nginx/sites-enabled",
    "template": "nginx/default.temp",
    "acme_template": "nginx/acme_challenge.temp"
  }
}
```

* `domain` – base domain used for main site and subdomains
* `email` – address passed to certbot when requesting certificates
* `cron_days` – renew certificates this many days before they expire when running in `cron` mode
* `paths.nginx` – directory where nginx site configs are stored
* `paths.template` – template file for the final nginx config
* `paths.acme_template` – template used during certificate issuance

To keep certificates up to date automatically, schedule the cron mode. A typical cron entry might look like:

```cron
0 * * * * /usr/bin/python3 /path/to/certbot-nginx-manager/main.py cron
```

Replace the path with the location of your project.

## Usage

Run the CLI script:

```bash
python main.py <mode> [options]
```

### Modes

#### `create`

Create a new Nginx + Certbot configuration for a (sub)domain.

```bash
python main.py create blog --port 3000
python main.py create --main --port 8080
```

#### `update`

Manually update the certificate for a domain:

```bash
python main.py update blog
python main.py update --main
```

#### `cron`

Check all installed certificates and renew those expiring within the configured number of days:

```bash
python main.py cron
```

> Intended to be run periodically via `cron` or systemd timers.

## Templates

You must provide two template files in the `nginx/` folder:

* `default.temp` — for full nginx + proxy config
* `acme_challenge.temp` — for `.well-known/acme-challenge/` validation

Each template should include `{{DOMAIN}}` and `{{PORT}}` placeholders where appropriate.
