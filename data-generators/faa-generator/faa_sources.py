import getpass
import re
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import paramiko
import requests
from bs4 import BeautifulSoup


def retry_with_backoff(max_retries=5, base_delay=2, max_delay=120, backoff_factor=2):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay after each retry
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        print(f"✗ Failed after {max_retries + 1} attempts: {e}")
                        raise last_exception
                    
                    # Determine if this is a connection error that needs longer delays
                    error_str = str(e).lower()
                    is_connection_error = any(term in error_str for term in [
                        'connection refused', 'connection reset', 'timeout', 
                        'max retries exceeded', 'newconnectionerror'
                    ])
                    
                    if is_connection_error:
                        # Use longer delays for connection issues
                        delay = min(delay * backoff_factor, max_delay)
                        print(f"⚠️  Attempt {attempt + 1} failed (connection issue): {e}")
                        print(f"🔄 Retrying in {delay} seconds...")
                    else:
                        # Use shorter delays for other errors
                        delay = min(delay * backoff_factor, max_delay // 2)
                        print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                        print(f"🔄 Retrying in {delay} seconds...")
                    
                    time.sleep(delay)
            
            return None
        return wrapper
    return decorator


class FaaSource(ABC):
    @abstractmethod
    def list_faa_paths(self):
        pass

    @abstractmethod
    def fetch_faa_content(self, path):
        pass


class FtpFaaSource(FaaSource):
    def __init__(self, base_url, max_retries=5):
        self.base_url = base_url.rstrip("/")
        self.strain_ids = []
        self.max_retries = max_retries
        self.session = requests.Session()
        # Configure session with retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @retry_with_backoff(max_retries=5, base_delay=3, max_delay=60)
    def list_faa_paths(self):
        response = self.session.get(self.base_url, timeout=60)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        self.strain_ids = [
            a["href"].rstrip("/")
            for a in soup.find_all("a", href=True)
            if re.match(r"^[A-Z]{2}_.+/$", a["href"])
        ]
        return [
            (
                strain_id,
                f"{self.base_url}/{strain_id}/functional_annotation/prokka/{strain_id}.faa",
            )
            for strain_id in self.strain_ids
        ]

    @retry_with_backoff(max_retries=5, base_delay=2, max_delay=60)
    def fetch_faa_content(self, url):
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        return response.text


class SftpFaaSource(FaaSource):
    def __init__(self, host, port, base_dirs, username, max_retries=3):
        self.host = host
        self.port = port
        self.base_dirs = base_dirs
        self.username = username
        self.password = getpass.getpass(f"SFTP password for {username}@{host}: ")
        self.faa_files = []
        self._thread_local = threading.local()
        self.max_retries = max_retries

    def _get_sftp_client(self):
        if not hasattr(self._thread_local, "sftp"):
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            self._thread_local.transport = transport
            self._thread_local.sftp = sftp
        return self._thread_local.sftp

    @retry_with_backoff(max_retries=3, base_delay=2, max_delay=30)
    def list_faa_paths(self):
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
                    faa_path = (
                        f"{base_dir}/{sub}/functional_annotation/prokka/{sub}.faa"
                    )
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

    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=20)
    def fetch_faa_content(self, path):
        print(f"⬇️ Fetching: {path}")
        sftp = self._get_sftp_client()
        with sftp.file(path, "r") as remote_file:
            content = remote_file.read().decode("utf-8")
        print(f"✅ Done: {path}")
        return content

    def __del__(self):
        if hasattr(self, "_thread_local"):
            if hasattr(self._thread_local, "sftp"):
                self._thread_local.sftp.close()
            if hasattr(self._thread_local, "transport"):
                self._thread_local.transport.close()


class FaaConsolidator:
    def __init__(
        self,
        sources,
        output_dir="output",
        output_filename="all_proteins_codon_both_species.faa",
        max_workers=2,  # Reduced from 3 to 2 to be gentler on the server
    ):
        self.sources = sources
        self.output_dir = Path(output_dir)
        self.output_file = self.output_dir / output_filename
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers

    def fetch_task(self, source, name, path):
        print(f"⬇️ Fetching: {path}")
        try:
            content = source.fetch_faa_content(path)
            if content:
                return (name, content)
            else:
                print(f"⚠️  Empty content for {name}, skipping...")
                return None
        except Exception as e:
            error_str = str(e).lower()
            if 'connection refused' in error_str or 'max retries exceeded' in error_str:
                print(f"✗ Connection failed for {name} after all retries, skipping...")
            else:
                print(f"✗ Failed to fetch {name} from {path}: {e}")
            return None

    def _process_source_parallel(self, source):
        """Handle downloading content in parallel for a single source."""
        results = []
        tasks = []
        faa_paths = source.list_faa_paths()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for name, path in faa_paths:
                tasks.append(executor.submit(self.fetch_task, source, name, path))

            for future in as_completed(tasks):
                result = future.result()
                if result is not None:
                    results.append(result)
        return results

    def consolidate(self):
        all_results = []
        total_attempted = 0
        total_successful = 0

        with ThreadPoolExecutor(max_workers=len(self.sources)) as outer_executor:
            future_to_source = {
                outer_executor.submit(self._process_source_parallel, source): source
                for source in self.sources
            }
            for future in as_completed(future_to_source):
                result = future.result()
                all_results.extend(result)

        # Count total files attempted (this is approximate since we don't track individual failures)
        for source in self.sources:
            if hasattr(source, 'strain_ids'):
                total_attempted += len(source.strain_ids)
            elif hasattr(source, 'faa_files'):
                total_attempted += len(source.faa_files)

        total_successful = len(all_results)
        failed_count = total_attempted - total_successful

        print(f"📊 Processing Summary:")
        print(f"   • Total files attempted: {total_attempted}")
        print(f"   • Successfully processed: {total_successful}")
        print(f"   • Failed/skipped: {failed_count}")
        print(f"   • Success rate: {(total_successful/total_attempted*100):.1f}%" if total_attempted > 0 else "   • Success rate: N/A")

        print(f"\nWriting {len(all_results)} .faa entries to output")
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
            "/hps/nobackup/rdf/metagenomics/service-team/users/tgurbich/Misc/Flagship/MAGs_for_pangenomes_Fall2024/spire_vulgatus_mags_mettannotator_results2",
        ],
    )

    consolidator = FaaConsolidator(
        sources=[
            FtpFaaSource(ftp_url),
            sftp_source,
        ],
        max_workers=3,
    )

    consolidator.consolidate()
