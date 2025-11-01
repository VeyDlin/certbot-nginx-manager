import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from config import Config
from certbot_manager import CertbotManager
from nginx_manager import NginxManager


logger = logging.getLogger(__name__)


def get_full_domain(config: Config, subdomain: str | None, is_main: bool):
    if is_main or subdomain is None:
        return config.domain
    return f"{subdomain}.{config.domain}"


def run_update_mode(config: Config, subdomain: str | None, is_main: bool):
    domain = get_full_domain(config, subdomain, is_main)
    logger.info("Updating certificate for %s", domain)
    nginx = NginxManager(domain, None, config.paths.nginx, config.paths.template, config.paths.acme_template)

    if not nginx.extract_port_from_config():
        logger.error("Failed to extract port from config")
        return
    
    if not nginx.create_backup():
        logger.error("Config file for %s does not exist. Cannot create backup.", domain)
        return
    
    if not nginx.create_acme_challenge_config():
        logger.error("Failed to create ACME challenge config for %s", domain)
        nginx.restore_backup()
        return
    
    if not NginxManager.test_config():
        logger.error("nginx config test failed after writing ACME config")
        nginx.restore_backup()
        return

    if not NginxManager.reload():
        logger.error("Failed to reload nginx after writing ACME config")
        nginx.restore_backup()
        return
    
    if not CertbotManager.request_basic_certificate(domain, config.email):
        logger.error("Failed to obtain certificate from certbot for %s", domain)

    nginx.restore_backup()
    
    if not NginxManager.reload():
        logger.warning("nginx reloaded with restored config but may require manual attention")

    
def run_create_mode(config: Config, subdomain: str | None, is_main: bool, port: str):
    domain = get_full_domain(config, subdomain, is_main)
    logger.info("Creating new certificate for %s on port %s", domain, port)
    nginx = NginxManager(domain, port, config.paths.nginx, config.paths.template, config.paths.acme_template)

    if nginx.config_exists():
        logger.error("Config already exists for %s. Aborting.", domain)
        return
    
    if not nginx.create_acme_challenge_config():
        logger.error("Failed to create ACME challenge config for %s", domain)
        nginx.delete_config()
        return
    
    if not NginxManager.test_config():
        logger.error("nginx config test failed after writing ACME config")
        nginx.delete_config()
        return

    if not NginxManager.reload():
        logger.error("Failed to reload nginx after writing ACME config")
        nginx.delete_config()
        return
    
    if not CertbotManager.request_basic_certificate(domain, config.email):
        logger.error("Failed to obtain certificate from certbot for %s", domain)
        nginx.delete_config()
        NginxManager.reload()
        return

    nginx.delete_config()

    if not NginxManager.reload():
        logger.warning("nginx reloaded with restored config but may require manual attention")
        return

    if not nginx.create_config():
        logger.error("Failed to create nginx config")
        return

    if not NginxManager.test_config():
        logger.error("nginx config test failed after initial config creation")
        nginx.delete_config()
        return

    if not NginxManager.reload():
        logger.error("Failed to reload nginx after initial config creation")
        nginx.delete_config()
        return


def run_cron_mode(config: Config):
    logger.info("Running in cron mode")
    current_time = datetime.now(timezone.utc)
    for cert in CertbotManager.list_certificates():
        time_remaining = cert.expiry_date - current_time
        if time_remaining <= timedelta(days=config.cron_days):
            logger.info("Certificate '%s' expires in %d day(s). Updating...", cert.domains, time_remaining.days)
            if cert.domains == config.domain:
                run_update_mode(config, None, True)
            elif cert.domains.endswith("." + config.domain):
                sub = cert.domains.removesuffix("." + config.domain)
                run_update_mode(config, sub, False)

            
def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Manage Nginx and Certbot for domains")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    cron_parser = subparsers.add_parser("cron", help="Auto-renew certificates if near expiration")
    cron_parser.add_argument("--config", type=Path, default=Path("config.json"))

    update_parser = subparsers.add_parser("update", help="Manually update certificate for given domain")
    update_parser.add_argument("subdomain", nargs="?", help="Subdomain")
    update_parser.add_argument("--main", action="store_true")
    update_parser.add_argument("--config", type=Path, default=Path("config.json"))

    create_parser = subparsers.add_parser("create", help="Create a new certificate")
    create_parser.add_argument("subdomain", nargs="?", help="Subdomain")
    create_parser.add_argument("--main", action="store_true")
    create_parser.add_argument("--port", required=True)
    create_parser.add_argument("--config", type=Path, default=Path("config.json"))

    args = parser.parse_args()

    config = Config.load_from_file(args.config)

    if args.mode == "cron":
        run_cron_mode(config)

    elif args.mode == "update":
        if not args.main and not args.subdomain:
            logger.error("Either --main or a subdomain must be specified for update mode.")
            sys.exit(1)
        run_update_mode(config, args.subdomain, args.main)

    elif args.mode == "create":
        if not args.main and not args.subdomain:
            logger.error("Either --main or a subdomain must be specified for create mode.")
            sys.exit(1)
        run_create_mode(config, args.subdomain, args.main, args.port)


if __name__ == "__main__":
    main()
