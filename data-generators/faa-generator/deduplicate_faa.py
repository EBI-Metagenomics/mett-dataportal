import hashlib
import json

from Bio import SeqIO


def deduplicate_faa(input_faa, output_faa, type_strains=None):
    dedup_map = {}

    print(f"🔍 Deduplicating from: {input_faa}")
    type_strains = set(type_strains or [])

    with open(output_faa, "w") as out_handle:
        for record in SeqIO.parse(input_faa, "fasta"):
            seq_str = str(record.seq)
            seq_hash = hashlib.sha256(seq_str.encode()).hexdigest()
            acc = record.id
            descr = record.description
            meta_entry = {"acc": acc, "descr": descr}

            if seq_hash not in dedup_map:
                is_type = any(ts in acc for ts in type_strains)
                dedup_map[seq_hash] = {
                    "rep": record,
                    "meta": [meta_entry],
                    "is_type": is_type,
                }
            else:
                dedup_map[seq_hash]["meta"].append(meta_entry)
                if not dedup_map[seq_hash]["is_type"] and any(
                    ts in acc for ts in type_strains
                ):
                    dedup_map[seq_hash]["rep"] = record
                    dedup_map[seq_hash]["is_type"] = True

        print(f"✅ Unique sequences: {len(dedup_map)}")

        for entry in dedup_map.values():
            rep = entry["rep"]
            rep_id = rep.id
            rep_desc = rep.description.split(maxsplit=1)[-1]
            metadata = json.dumps(entry["meta"], separators=(",", ":"))
            rep.description = f"{rep_desc} {metadata}"
            rep.name = rep.id = rep_id
            SeqIO.write(rep, out_handle, "fasta")

    print(f"✔ Written deduplicated output to: {output_faa}")
