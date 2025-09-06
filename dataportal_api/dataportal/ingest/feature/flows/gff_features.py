# ingest/feature/flows/gff_features.py
import tempfile, os
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.feature.sources import ftp_connect, load_protein_seqs
from dataportal.ingest.feature.parsing import parse_dbxref
from dataportal.ingest.utils import normalize_strain_id, species_name_for_isolate, strain_prefix
from dataportal.models import FeatureDocument  # your ES DSL document

class GFFGenes(Flow):
    """
    Builds gene features from GFFs on FTP. IGs are created by Essentiality flow.
    Uses *raw* isolate names for FTP paths and *normalized* isolate ids in ES docs.
    """
    def __init__(self, ftp_server, ftp_root, index_name="feature_index", mapping=None):
        super().__init__(index_name)
        self.ftp_server = ftp_server
        self.ftp_root = ftp_root
        self.mapping = mapping or {}

    def run(self, raw_isolates: list[str], norm_isolates: list[str] | None = None):
        """
        raw_isolates: directory names as listed on FTP
        norm_isolates: normalized ids for ES (if None, we will normalize internally)
        """
        if norm_isolates is None:
            norm_isolates = [normalize_strain_id(s) for s in raw_isolates]

        # pair raw + normalized in order
        pairs = list(zip(raw_isolates, norm_isolates))

        ftp = ftp_connect(self.ftp_server)
        try:
            for raw_isolate, norm_isolate in pairs:
                self._ingest_isolate(ftp, raw_isolate, norm_isolate)
            self.flush()
        finally:
            ftp.quit()

    def _ingest_isolate(self, ftp, raw_isolate: str, norm_isolate: str):
        # FTP paths must use the raw directory name
        gff_dir = f"{self.ftp_root}/{raw_isolate}/functional_annotation/merged_gff/"
        try:
            gffs = [p for p in ftp.nlst(gff_dir) if p.endswith("_annotations.gff")]
        except Exception:
            return

        faa = f"{self.ftp_root}/{raw_isolate}/functional_annotation/prokka/{raw_isolate}.faa"
        protein_seqs = {}
        try:
            protein_seqs = load_protein_seqs(ftp, faa)
        except Exception:
            pass

        # taxonomy from normalized isolate id
        sp_name = species_name_for_isolate(norm_isolate)
        sp_acronym = strain_prefix(norm_isolate)

        for remote in gffs:
            self._ingest_gff_file(ftp, remote, raw_isolate, norm_isolate, sp_acronym, sp_name, protein_seqs)

    def _ingest_gff_file(self, ftp, remote, raw_isolate, norm_isolate, sp_acronym, sp_name, prot_seqs):
        local = tempfile.NamedTemporaryFile(delete=False)
        try:
            with open(local.name, "wb") as out:
                ftp.retrbinary(f"RETR {remote}", out.write)
            with open(local.name, "r") as f:
                for line in f:
                    if not line or line.startswith("#"):
                        continue
                    cols = line.rstrip("\n").split("\t")
                    if len(cols) != 9 or cols[2] != "gene":
                        continue
                    seq_id, _, _, start, end, _, strand, _, attributes = cols
                    attr = dict(item.split("=", 1) for item in attributes.split(";") if "=" in item)

                    locus_tag = attr.get("locus_tag")
                    if not locus_tag:
                        continue

                    dbxref, uniprot_id, cog_id = parse_dbxref(attr.get("Dbxref", ""))

                    doc = FeatureDocument(
                        meta={"id": locus_tag},
                        feature_id=locus_tag,
                        feature_type="gene",
                        element="gene",
                        locus_tag=locus_tag,
                        uniprot_id=uniprot_id,
                        seq_id=seq_id,
                        start=int(start),
                        end=int(end),
                        strand=strand,
                        gene_name=attr.get("Name"),
                        alias=[a for a in attr.get("Alias", "").split(",") if a],
                        product=attr.get("product"),
                        product_source=attr.get("product_source"),
                        inference=attr.get("inference"),
                        eggnog=attr.get("eggNOG") or attr.get("eggnog"),
                        species_scientific_name=sp_name,
                        species_acronym=sp_acronym,
                        isolate_name=norm_isolate,          # <-- normalized for ES linking
                        kegg=[x for x in attr.get("kegg", "").split(",") if x],
                        pfam=[x for x in attr.get("pfam", "").split(",") if x],
                        interpro=[x for x in attr.get("interpro", "").split(",") if x],
                        dbxref=dbxref,
                        ec_number=attr.get("eC_number"),
                        cog_id=[cog_id] if cog_id else [],
                        cog_funcats=[x for x in attr.get("cog", "").split(",") if x],
                        protein_sequence=prot_seqs.get(locus_tag, ""),
                        has_reactions=False, has_proteomics=False, has_fitness=False, has_mutant_growth=False,
                    )
                    doc.meta.index = self.index
                    self.add(doc.to_dict(include_meta=True))
        finally:
            try:
                os.unlink(local.name)
            except Exception:
                pass
