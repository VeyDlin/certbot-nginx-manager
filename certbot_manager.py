import subprocess
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Certificate:
    certificate_name: str
    serial_number: str
    key_type: str
    domains: str
    expiry_date: datetime
    certificate_path: str
    private_key_path: str

class CertbotManager:
    @staticmethod
    def request_basic_certificate(domain: str, email: str) -> bool:
        command = [
            "certbot", "--nginx",
            "-d", domain,
            "--email", email,
            "--agree-tos",
            "--non-interactive",
            "--redirect"
        ]
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0

    @staticmethod
    def list_certificates() -> List[Certificate]:
        result = subprocess.run(["certbot", "certificates"], capture_output=True, text=True)
        return CertbotManager._parse_certbot_output(result.stdout)

    @staticmethod
    def _parse_certbot_output(output: str) -> List[Certificate]:
        certs: List[Certificate] = []
        cert_data: Dict[str, Any] = {}
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Certificate Name:"):
                if cert_data:
                    certs.append(Certificate(**cert_data))
                cert_data = {"certificate_name": line.split(": ")[1]}
            elif line.startswith("Serial Number:"):
                cert_data["serial_number"] = line.split(": ")[1]
            elif line.startswith("Key Type:"):
                cert_data["key_type"] = line.split(": ")[1]
            elif line.startswith("Domains:"):
                cert_data["domains"] = line.split(": ")[1]
            elif line.startswith("Expiry Date:"):
                date_str = line.split(": ")[1].split(" (")[0]
                cert_data["expiry_date"] = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z")
            elif line.startswith("Certificate Path:"):
                cert_data["certificate_path"] = line.split(": ")[1]
            elif line.startswith("Private Key Path:"):
                cert_data["private_key_path"] = line.split(": ")[1]
        if cert_data:
            certs.append(Certificate(**cert_data))
        return certs
