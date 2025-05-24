import logging
import re
from pathlib import Path
import shutil
import subprocess


logger = logging.getLogger(__name__)


class NginxManager:
    nginx_dir = Path("/etc/nginx/sites-enabled")
    template_path = Path("nginx/default.temp")
    acme_template_path = Path("nginx/acme_challenge.temp")

    def __init__(self, domain: str, port: str | None, nginx_dir: Path, template_path: Path, acme_template_path: Path):
        self.domain = domain
        self.port = port
        self.nginx_dir = nginx_dir
        self.template_path = template_path
        self.acme_template_path = acme_template_path
        self.config_path = self.nginx_dir / f"{self.domain}.conf"
        self.backup_path = self.config_path.with_suffix(".conf.bak")

    def extract_port_from_config(self) -> str:
        if not self.config_exists():
            return False

        content = self.config_path.read_text()

        match_with_port = re.search(r'proxy_pass\s+https?://[^:\s]+:(\d+);', content)
        if match_with_port:
            self.port = match_with_port.group(1)
            return self.port

        match_without_port = re.search(r'proxy_pass\s+(https?)://[^;\s/]+;', content)
        if match_without_port:
            scheme = match_without_port.group(1)
            self.port = "443" if scheme == "https" else "80"
            return self.port

        return True
    
    def create_config(self):
        if not self.template_path.exists():
            return False
        
        content = self.template_path.read_text()
        rendered = content.replace("{{DOMAIN}}", self.domain).replace("{{PORT}}", self.port)
        self.config_path.write_text(rendered)
        logger.info("Nginx config created: %s", self.config_path)
        return True

    def create_acme_challenge_config(self):
        if not self.acme_template_path.exists():
            return False
        
        content = self.acme_template_path.read_text()
        rendered = content.replace("{{DOMAIN}}", self.domain)
        self.config_path.write_text(rendered)
        logger.info("ACME challenge config created: %s", self.config_path)
        return True

    def config_exists(self) -> bool:
        return self.config_path.exists()

    def backup_exists(self) -> bool:
        return self.backup_path.exists()

    def create_backup(self) -> bool:
        if not self.config_exists():
            return False
        shutil.copy2(self.config_path, self.backup_path)
        logger.info("Backup created: %s", self.backup_path)
        return True

    def restore_backup(self):
        if not self.backup_exists():
            return False
        shutil.copy2(self.backup_path, self.config_path)
        logger.info("Backup restored to: %s", self.config_path)
        self.backup_path.unlink()
        logger.info("Backup deleted: %s", self.backup_path)
        return True

    def delete_backup(self):
        if self.backup_exists():
            self.backup_path.unlink()
            logger.info("Backup deleted: %s", self.backup_path)

    def delete_config(self):
        if self.config_exists():
            self.config_path.unlink()
            logger.info("Config deleted: %s", self.config_path)

    @staticmethod
    def test_config() -> bool:
        result = subprocess.run(["nginx", "-t"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            logger.info("nginx configuration is valid")
            return True
        logger.error("nginx configuration test failed")
        return False

    @staticmethod
    def reload() -> bool:
        result = subprocess.run(["systemctl", "reload", "nginx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            logger.info("nginx reloaded")
            return True
        logger.error("failed to reload nginx")
        return False
