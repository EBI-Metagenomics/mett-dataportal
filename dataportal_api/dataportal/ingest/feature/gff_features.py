import tempfile
import os
from dataportal.ingest.flow import Flow
from dataportal.ingest.feature.sources import (
    ftp_connect,
    is_primary_annotations_gff,
    list_isolates_from_ftp_session,
    list_isolates_from_local,
    load_protein_seqs,
    load_protein_seqs_from_file,
)
from dataportal.ingest.feature.parsing import parse_gene_gff_annotations
from dataportal.ingest.ftp_paths import (
    DEFAULT_FAA_PATH_TEMPLATE,
    DEFAULT_GFF_DIR_TEMPLATE,
    format_ftp_path,
)
from dataportal.ingest.utils import (
    parse_dbxref,
    species_name_for_isolate,
    strain_prefix,
)
from dataportal.models import FeatureDocument  # your ES DSL document


class GFFGenes(Flow):
    """
    Builds gene features from GFFs on FTP. IGs are created by Essentiality flow.
    Uses raw isolate names for both FTP paths and ES docs.
    """

    def __init__(
        self,
        ftp_server,
        ftp_root,
        index_name="feature_index",
        mapping=None,
        gff_dir_template=DEFAULT_GFF_DIR_TEMPLATE,
        faa_path_template=DEFAULT_FAA_PATH_TEMPLATE,
        local_root=None,
    ):
        super().__init__(index_name)
        self.ftp_server = ftp_server
        self.ftp_root = ftp_root
        self.local_root = (local_root or "").rstrip("/") or None
        self.mapping = mapping or {}
        self.gff_dir_template = gff_dir_template or DEFAULT_GFF_DIR_TEMPLATE
        self.faa_path_template = faa_path_template or DEFAULT_FAA_PATH_TEMPLATE

    def _source_root(self) -> str:
        return self.local_root or self.ftp_root

    def run(self, raw_isolates: list[str], norm_isolates: list[str] | None = None):
        """
        raw_isolates: directory names as listed on FTP
        norm_isolates: not used anymore - we use raw names directly
        """
        # Use raw isolate names directly
        pairs = [(raw_isolate, raw_isolate) for raw_isolate in raw_isolates]
        source_root = self._source_root()
        ftp = None
        if not self.local_root:
            ftp = ftp_connect(self.ftp_server)
        try:
            isolates = [raw for raw, _ in pairs]
            if not isolates:
                print(f"[import_features] listing isolate folders under {source_root}")
                if self.local_root:
                    isolates = list_isolates_from_local(self.local_root)
                else:
                    isolates = list_isolates_from_ftp_session(ftp, self.ftp_root)
                pairs = [(raw_isolate, raw_isolate) for raw_isolate in isolates]
            print(f"[import_features] {len(pairs)} isolate(s) to ingest")
            if not pairs:
                raise RuntimeError(
                    f"No isolate folders found under {source_root}. "
                    "Pass --isolates NAME ... or check --local-root / --ftp-root."
                )
            ingested = 0
            skipped = 0
            for raw_isolate, norm_isolate in pairs:
                if self._ingest_isolate(ftp, raw_isolate, norm_isolate):
                    ingested += 1
                else:
                    skipped += 1
            pending = len(self.buffer)
            self.flush()
            print(
                f"[import_features] finished: {ingested} with GFF, {skipped} skipped "
                f"(flushed last {pending} features)"
            )
        finally:
            if ftp is not None:
                try:
                    ftp.quit()
                except Exception:
                    try:
                        ftp.close()
                    except Exception:
                        pass

    def _ingest_isolate(self, ftp, raw_isolate: str, norm_isolate: str) -> bool:
        gff_dir = format_ftp_path(
            self.gff_dir_template, base=self._source_root(), isolate=raw_isolate
        )
        try:
            if self.local_root:
                listed = [
                    os.path.join(gff_dir, name)
                    for name in os.listdir(gff_dir)
                    if os.path.isfile(os.path.join(gff_dir, name))
                ]
            else:
                listed = ftp.nlst(gff_dir)
        except Exception as exc:
            print(
                f"[import_features] skip {raw_isolate}: cannot list {gff_dir} ({exc})"
            )
            return False

        gffs = [p for p in listed if is_primary_annotations_gff(p)]
        if not gffs:
            print(
                f"[import_features] skip {raw_isolate}: no *_annotations.gff in {gff_dir}"
            )
            return False

        faa = format_ftp_path(
            self.faa_path_template, base=self._source_root(), isolate=raw_isolate
        )
        protein_seqs = {}
        try:
            if self.local_root:
                protein_seqs = load_protein_seqs_from_file(faa)
            else:
                protein_seqs = load_protein_seqs(ftp, faa)
        except Exception as exc:
            print(f"[import_features] {raw_isolate}: no protein FASTA at {faa} ({exc})")

        sp_name = species_name_for_isolate(raw_isolate)
        sp_acronym = strain_prefix(raw_isolate)
        print(f"[import_features] {raw_isolate}: {os.path.basename(gffs[0])}")

        for remote in gffs:
            self._ingest_gff_file(
                ftp,
                remote,
                raw_isolate,
                norm_isolate,
                sp_acronym,
                sp_name,
                protein_seqs,
            )
        return True

    def parse_amr_attributes(self, attr_dict):
        """Extract AMR-related fields from GFF attributes dict and return a list of AMR dicts."""
        element_type = attr_dict.get("element_type", "").upper()
        if element_type != "AMR":
            return [], False

        amr_entry = {
            "gene_symbol": attr_dict.get("amrfinderplus_gene_symbol"),
            "sequence_name": attr_dict.get("amrfinderplus_sequence_name"),
            "scope": attr_dict.get("amrfinderplus_scope"),
            "element_type": attr_dict.get("element_type"),
            "element_subtype": attr_dict.get("element_subtype"),
            "drug_class": attr_dict.get("drug_class"),
            "drug_subclass": attr_dict.get("drug_subclass"),
            "uf_keyword": [
                kw.strip()
                for kw in attr_dict.get("uf_keyword", "").split(",")
                if kw.strip()
            ],
            "uf_ecnumber": attr_dict.get("uf_prot_rec_ecnumber"),
        }

        return [amr_entry], True

    def _ingest_gff_file(
        self, ftp, remote, raw_isolate, norm_isolate, sp_acronym, sp_name, prot_seqs
    ):
        gene_count = 0
        gff_path = None
        try:
            if self.local_root:
                gff_path = remote
            else:
                tmp = tempfile.NamedTemporaryFile(delete=False)
                gff_path = tmp.name
                tmp.close()
                with open(gff_path, "wb") as out:
                    ftp.retrbinary(f"RETR {remote}", out.write)
            with open(gff_path, "r") as f:
                for line in f:
                    if not line or line.startswith("#"):
                        continue
                    cols = line.rstrip("\n").split("\t")
                    if len(cols) != 9 or cols[2] != "gene":
                        continue
                    seq_id, _, _, start, end, _, strand, _, attributes = cols
                    attr = dict(
                        item.split("=", 1)
                        for item in attributes.split(";")
                        if "=" in item
                    )

                    locus_tag = attr.get("locus_tag")
                    if not locus_tag:
                        continue

                    amr_entries, has_amr_info = self.parse_amr_attributes(attr)
                    dbxref, uniprot_id, cog_id = parse_dbxref(attr.get("Dbxref", ""))

                    ontology_terms = [
                        {
                            "ontology_type": "GO",
                            "ontology_id": term,
                            "ontology_description": None,
                        }
                        for term in attr.get("Ontology_term", "").split(",")
                        if term
                    ]

                    uf_ontology_terms = (
                        attr.get("uf_ontology_term", "").split(",")
                        if "uf_ontology_term" in attr
                        else []
                    )
                    uf_prot_rec_fullname = attr.get("uf_prot_rec_fullname")
                    gff_annotations = parse_gene_gff_annotations(attr)

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
                        isolate_name=raw_isolate,  # <-- use raw isolate name
                        kegg=[x for x in attr.get("kegg", "").split(",") if x],
                        pfam=[x for x in attr.get("pfam", "").split(",") if x],
                        interpro=[x for x in attr.get("interpro", "").split(",") if x],
                        has_amr_info=has_amr_info,
                        amr=amr_entries,
                        dbxref=dbxref,
                        ec_number=attr.get("eC_number"),
                        uf_prot_rec_ecnumber=attr.get("uf_prot_rec_ecnumber"),
                        **gff_annotations,
                        cog_id=[cog_id] if cog_id else [],
                        cog_funcats=[x for x in attr.get("cog", "").split(",") if x],
                        protein_sequence=prot_seqs.get(locus_tag, ""),
                        has_reactions=False,
                        has_proteomics=False,
                        has_fitness=False,
                        has_mutant_growth=False,
                        ontology_terms=ontology_terms,
                        uf_ontology_terms=uf_ontology_terms,
                        uf_prot_rec_fullname=uf_prot_rec_fullname,
                    )
                    doc.meta.index = self.index
                    self.add(doc.to_dict(include_meta=True))
                    gene_count += 1
            if gene_count == 0:
                print(
                    f"[import_features] {raw_isolate}: 0 gene rows in "
                    f"{os.path.basename(remote)} (CDS-only GFFs need gene features added first)"
                )
            else:
                print(f"[import_features] {raw_isolate}: indexed {gene_count} genes")
        finally:
            if not self.local_root and gff_path:
                try:
                    os.unlink(gff_path)
                except Exception:
                    pass
