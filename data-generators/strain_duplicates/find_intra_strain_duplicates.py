import csv
import hashlib
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from bs4 import BeautifulSoup


class IntraStrainDuplicateFinder:
    def __init__(self, base_url, max_workers=3):
        self.base_url = base_url.rstrip("/")
        self.max_workers = max_workers

    def log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] {message}")

    def list_strain_faa_urls(self):
        """Fetch strain IDs and construct .faa file URLs."""
        self.log(f"Fetching strain list from: {self.base_url}")
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            strain_ids = [
                a["href"].rstrip("/")
                for a in soup.find_all("a", href=True)
                if re.match(r"^[A-Z]{2}_.+/$", a["href"])
            ]
            self.log(f"✓ Found {len(strain_ids)} strains")
            return [
                (
                    strain_id,
                    f"{self.base_url}/{strain_id}/functional_annotation/prokka/{strain_id}.faa",
                )
                for strain_id in strain_ids
            ]
        except requests.RequestException as e:
            self.log(f"✗ Error fetching strain list: {e}")
            return []

    def fetch_faa_content(self, strain_id, url):
        self.log(f"⬇️ Downloading {strain_id} from {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            return strain_id, response.text
        except requests.RequestException as e:
            self.log(f"✗ Failed to fetch {strain_id}: {e}")
            return strain_id, ""

    def parse_fasta(self, fasta_text):
        """Parse FASTA content into (gene_id, sequence) pairs."""
        records = []
        gene_id = None
        seq_lines = []
        for line in fasta_text.strip().splitlines():
            line = line.strip()
            if line.startswith(">"):
                if gene_id is not None:
                    records.append((gene_id, "".join(seq_lines)))
                gene_id = line.split()[0][1:]  # Remove '>' and keep only gene ID
                seq_lines = []
            else:
                seq_lines.append(line)
        if gene_id is not None:
            records.append((gene_id, "".join(seq_lines)))
        return records

    def find_duplicates_in_strain(self, strain_id, fasta_text):
        records = self.parse_fasta(fasta_text)
        self.log(f"🔬 {strain_id}: Parsed {len(records)} proteins")
        seq_to_genes = defaultdict(set)
        all_gene_ids = set()

        for gene_id, seq in records:
            seq_to_genes[seq].add(gene_id)
            all_gene_ids.add(gene_id)

        duplicates = {seq: genes for seq, genes in seq_to_genes.items() if len(genes) > 1}
        total_genes = len(all_gene_ids)
        total_proteins = len(records)
        total_dup_gene_ids = sum(len(genes) for genes in duplicates.values())

        if duplicates:
            self.log(
                f"⚠️  {strain_id}: Found {len(duplicates)} duplicated sequences involving {total_dup_gene_ids} gene IDs")
        else:
            self.log(f"✅ {strain_id}: No duplicates found")

        return {
            "strain_id": strain_id,
            "total_proteins": total_proteins,
            "total_genes": total_genes,
            "num_duplicates": len(duplicates),
            "total_duplicated_gene_ids": total_dup_gene_ids,
            "duplicated_sequences": duplicates,
        }

    def run(self):
        results = []
        strain_urls = self.list_strain_faa_urls()

        if not strain_urls:
            self.log("✗ No strain files found. Aborting.")
            return []

        self.log("🚀 Starting parallel download and analysis...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.fetch_faa_content, strain_id, url): strain_id
                for strain_id, url in strain_urls
            }
            for future in as_completed(futures):
                strain_id, content = future.result()
                if content:
                    result = self.find_duplicates_in_strain(strain_id, content)
                    if result["num_duplicates"] > 0:
                        results.append(result)

        self.log("🎯 Finished processing all strains.")
        return results


def write_csv_outputs(results, out_dir="output"):
    import os
    os.makedirs(out_dir, exist_ok=True)

    summary_path = os.path.join(out_dir, "intra_strain_duplicates_summary.csv")
    details_path = os.path.join(out_dir, "intra_strain_duplicates_details.csv")

    # --- Write summary ---
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Strain ID", "Num Duplicated Sequences", "Total Duplicated Gene IDs"])
        for r in results:
            writer.writerow([r["strain_id"], r["num_duplicates"], r["total_duplicated_gene_ids"]])

    # --- Write details ---
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Strain ID",
            "Total Proteins",
            "Total Unique Genes",
            "Duplicated Sequences",
            "Duplicated Gene IDs",
            "Duplication % (by gene)"
        ])
        for r in results:
            perc = (r["total_duplicated_gene_ids"] / r["total_genes"] * 100) if r["total_genes"] else 0
            writer.writerow([
                r["strain_id"],
                r["total_proteins"],
                r["total_genes"],
                r["num_duplicates"],
                r["total_duplicated_gene_ids"],
                f"{perc:.2f}"
            ])

    print(f"\n📁 CSV files saved to '{out_dir}':")
    print(f"  • Summary: {summary_path}")
    print(f"  • Details: {details_path}")


if __name__ == "__main__":
    base_url = "https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15"
    finder = IntraStrainDuplicateFinder(base_url)
    duplication_results = finder.run()

    if duplication_results:
        write_csv_outputs(duplication_results)
    else:
        print("✅ No duplicates found. No CSV generated.")
