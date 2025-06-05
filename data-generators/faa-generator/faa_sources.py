import getpass
import re
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import paramiko
import requests
from bs4 import BeautifulSoup


class FaaSource(ABC):
    @abstractmethod
    def list_faa_paths(self):
        pass

    @abstractmethod
    def fetch_faa_content(self, path):
        pass


class FtpFaaSource(FaaSource):
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.strain_ids = []

    def list_faa_paths(self):
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            self.strain_ids = [
                a['href'].rstrip('/')
                for a in soup.find_all('a', href=True)
                if re.match(r'^[A-Z]{2}_.+/$', a['href'])
            ]
            return [
                (strain_id, f"{self.base_url}/{strain_id}/functional_annotation/prokka/{strain_id}.faa")
                for strain_id in self.strain_ids
            ]
        except requests.RequestException as e:
            print(f"✗ Error fetching FTP strain list: {e}")
            return []

    def fetch_faa_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"✗ Failed to fetch FTP file: {url} — {e}")
            return ""


class SftpFaaSource(FaaSource):
    def __init__(self, host, port, base_dirs, username):
        self.host = host
        self.port = port
        self.base_dirs = base_dirs
        self.username = username
        self.password = getpass.getpass(f"SFTP password for {username}@{host}: ")
        self.faa_files = []
        self._thread_local = threading.local()

    def _get_sftp_client(self):
        if not hasattr(self._thread_local, "sftp"):
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            self._thread_local.transport = transport
            self._thread_local.sftp = sftp
        return self._thread_local.sftp

    def list_faa_paths(self):
        try:
            print("🔍 Connecting to SFTP...")
            transport = paramiko.Transport((self.host, self.port))

            print("🔐 Performing handshake...")
            transport.banner_timeout = 10
            transport.connect(username=self.username, password=self.password)
            print("✅ SFTP connected")

            sftp = paramiko.SFTPClient.from_transport(transport)

            for base_dir in self.base_dirs:
                print(f"📁 Scanning base directory: {base_dir}")
                try:
                    subfolders = sftp.listdir(base_dir)
                    print(f"   └─ Found {len(subfolders)} subfolders")
                    for sub in subfolders:
                        faa_path = f"{base_dir}/{sub}/functional_annotation/prokka/{sub}.faa"
                        try:
                            sftp.stat(faa_path)
                            self.faa_files.append((sub, faa_path))
                        except FileNotFoundError:
                            print(f"     ⛔ Missing: {faa_path}")
                            continue
                except FileNotFoundError as e:
                    print(f"✗ Invalid base directory: {base_dir} — {e}")
                    continue

            print(f"📦 Total .faa files found on SFTP: {len(self.faa_files)}")
            sftp.close()
            transport.close()
            return self.faa_files

        except Exception as e:
            print(f"Failed SFTP scan: {e}")
            return []

    def fetch_faa_content(self, path):
        try:
            print(f"⬇️ Fetching: {path}")
            sftp = self._get_sftp_client()
            with sftp.file(path, 'r') as remote_file:
                content = remote_file.read().decode('utf-8')
            print(f"✅ Done: {path}")
            return content
        except Exception as e:
            print(f"Failed to fetch SFTP file: {path} — {e}")
            return ""

    def __del__(self):
        if hasattr(self, "_thread_local"):
            if hasattr(self._thread_local, "sftp"):
                self._thread_local.sftp.close()
            if hasattr(self._thread_local, "transport"):
                self._thread_local.transport.close()


class FaaConsolidator:
    def __init__(self, sources, output_dir="output", output_filename="all_proteins_codon_both_species.faa",
                 max_workers=3):
        self.sources = sources
        self.output_dir = Path(output_dir)
        self.output_file = self.output_dir / output_filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers

    def fetch_task(self, source, name, path):
        print(f"⬇️ Fetching: {path}")
        return (name, source.fetch_faa_content(path))

    def _process_source_parallel(self, source):
        """Handle downloading content in parallel for a single source."""
        results = []
        tasks = []
        faa_paths = source.list_faa_paths()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for name, path in faa_paths:
                tasks.append(executor.submit(self.fetch_task, source, name, path))

            for future in as_completed(tasks):
                name, content = future.result()
                if content:
                    results.append((name, content))
        return results

    def consolidate(self):
        all_results = []

        with ThreadPoolExecutor(max_workers=len(self.sources)) as outer_executor:
            future_to_source = {
                outer_executor.submit(self._process_source_parallel, source): source
                for source in self.sources
            }
            for future in as_completed(future_to_source):
                result = future.result()
                all_results.extend(result)

        print(f"Writing {len(all_results)} .faa entries to output")
        with open(self.output_file, "w") as outfile:
            for name, content in all_results:
                outfile.write(content)
                outfile.write("\n")

        print(f"\n✔ Consolidated protein file saved to: {self.output_file.resolve()}")


if __name__ == "__main__":
    ftp_url = "http://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15"

    sftp_source = SftpFaaSource(
        host="codon-login",
        port=22,
        username="vikasg",
        base_dirs=[
            "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/spire_uniformis_mags_mettannotator_results",
            "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/mgnify_uniformis_mags_mettannotator_results",
            "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/mgnify_vulgatus_mags_mettannotator_results",
            "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/spire_vulgatus_mags_mettannotator_results2"
        ]
    )

    consolidator = FaaConsolidator(
        sources=[
            FtpFaaSource(ftp_url),
            sftp_source,
        ],
        max_workers=3
    )

    consolidator.consolidate()
