from fetch_and_consolidate import fetch_all_sequences, consolidate_filtered, generate_deduplicated_isolates
from deduplicate_faa import deduplicate_faa

TYPE_STRAINS = {"BU_ATCC8492", "PV_ATCC8482"}


def run_all():
    print("Preloading all sequences...")
    all_entries = fetch_all_sequences(use_sftp=False)  # change to True when needed

    # Generate deduplicated files per isolate
    print("\n🔄 Generating deduplicated files per isolate...")
    try:
        isolate_count = generate_deduplicated_isolates(all_entries)
        print(f"✅ Generated {isolate_count} deduplicated isolate files in output/isolates-db/")
    except Exception as e:
        print(f"✗ Failed to generate isolate files: {e}")

    combos = [
        ("bu_typestrains.faa", ["BU_"], True, "bu_typestrains_deduplicated.faa"),
        ("bu_all_strains.faa", ["BU_"], False, "bu_all_strains_deduplicated.faa"),
        ("pv_typestrains.faa", ["PV_"], True, "pv_typestrains_deduplicated.faa"),
        ("pv_all_strains.faa", ["PV_"], False, "pv_all_strains_deduplicated.faa"),
        (
            "bu_pv_typestrains.faa",
            ["BU_", "PV_"],
            True,
            "bu_pv_typestrains_deduplicated.faa",
        ),
        (
            "bu_pv_all_strains.faa",
            ["BU_", "PV_"],
            False,
            "bu_pv_all_strains_deduplicated.faa",
        ),
    ]

    for raw, prefixes, only_type, final in combos:
        print(f"\n▶ STEP: {final}")
        try:
            raw_path = consolidate_filtered(
                all_entries,
                output_filename=raw,
                strain_prefixes=prefixes,
                only_type_strains=only_type,
            )
            print(f"📁 Wrote raw file: {raw_path}")
        except Exception as e:
            print(f"Failed to consolidate for {final}: {e}")
            continue

        try:
            dedup_path = f"output/{final}"
            deduplicate_faa(raw_path, dedup_path, type_strains=TYPE_STRAINS)
        except Exception as e:
            print(f"Failed to deduplicate for {final}: {e}")


if __name__ == "__main__":
    run_all()
