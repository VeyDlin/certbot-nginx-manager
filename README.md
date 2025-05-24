# certbot-nginx-manager

A simple CLI utility for managing Nginx and Certbot certificates — with automatic renewal, manual updates, and new domain provisioning. Works with both root and subdomains.

## Features

- 🔒 Automatically renew expiring SSL certificates via `cron`
- ⚙️ Create and configure new HTTPS domains with Nginx + Certbot
- 🛠 Manually update certificates for specific domains
- 🧩 Uses JSON config to store paths, email, base domain, and renewal policy

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

Create a `config.json` file in the root directory:

```json
{
  "domain": "yourdomain.com",
  "email": "your@email.com",
  "cron_days": 2,
  "paths": {
    "nginx_dir": "/etc/nginx/sites-enabled",
    "template": "nginx/default.temp",
    "acme_template": "nginx/acme_challenge.temp"
  }
}
```

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
