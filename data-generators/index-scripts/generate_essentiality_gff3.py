import pandas as pd
import requests
import os

# FTP URLs
ftp_urls = {
    "BU_ATCC8492": "https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/BU_ATCC8492/functional_annotation/merged_gff/BU_ATCC8492_annotations.gff",
    "PV_ATCC8482": "https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/PV_ATCC8482/functional_annotation/merged_gff/PV_ATCC8482_annotations.gff",
}

# essentiality CSV file
essentiality_df = pd.read_csv(
    "../data/essentiality_table_all_libraries_240818_14102024.csv"
)


# Function to download GFF file from FTP
def download_gff(strain, url):
    response = requests.get(url)
    filename = f"{strain}_annotations.gff"
    with open(filename, "wb") as file:
        file.write(response.content)
    print(f"Downloaded: {filename}")
    return filename


#  parse the GFF file and create a mapping of locus_tag to seqid
def get_seqid_mapping(gff_filename):
    seqid_mapping = {}
    with open(gff_filename, "r") as file:
        for line in file:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 9:
                continue
            attributes = parts[8]
            seqid = parts[0]
            for attr in attributes.split(";"):
                if attr.startswith("locus_tag="):
                    locus_tag = attr.split("=")[1]
                    seqid_mapping[locus_tag] = seqid
    return seqid_mapping


# Function to create essentiality GFF3 DataFrame with correct seqid
def create_essentiality_gff(df, seqid_mapping):
    # Group by 'locus_tag', 'gene_name', 'start', and 'end'
    grouped_df = (
        df.groupby(["locus_tag", "gene_name", "start", "end"])
        .agg(
            {
                "final_essentiality_call_agreement": lambda x: list(x),
                "media": lambda x: list(x),
                "confidence_score_HMM": lambda x: list(x),
            }
        )
        .reset_index()
    )

    def combine_essentiality_and_confidence(row):
        essentiality_dict = {}
        confidence_dict = {}

        for essentiality, media, confidence in zip(
            row["final_essentiality_call_agreement"],
            row["media"],
            row["confidence_score_HMM"],
        ):
            media_key = media.capitalize()
            essentiality_dict[f"Essentiality_{media_key}"] = essentiality
            confidence_dict[f"Confidence_{media_key}"] = confidence

        combined_attributes = [
            f"{key}={value}"
            for key, value in {**essentiality_dict, **confidence_dict}.items()
        ]
        return ";".join(combined_attributes)

    grouped_df["combined_attributes"] = grouped_df.apply(
        combine_essentiality_and_confidence, axis=1
    )

    gff_df = pd.DataFrame(
        {
            "seqid": grouped_df["locus_tag"].map(seqid_mapping),
            "source": "essentiality_analysis",
            "type": "gene",
            "start": grouped_df["start"],
            "end": grouped_df["end"],
            "score": ".",  # Set to '.' since we have multiple confidence scores
            "strand": ".",  # Set to '.' if strand is not known
            "phase": ".",
            "attributes": grouped_df.apply(
                lambda row: f"ID={row['locus_tag']};Name={'' if row['gene_name'] == 'blank' else row['gene_name']};{row['combined_attributes']}",
                axis=1,
            ),
        }
    )

    return gff_df


# Generate essentiality GFF3 files for each strain
target_strains = ["BU_ATCC8492", "PV_ATCC8482"]

for strain in target_strains:
    # Download the annotation GFF file
    gff_filename = download_gff(strain, ftp_urls[strain])

    try:
        # Get the seqid mapping from the annotation GFF
        seqid_mapping = get_seqid_mapping(gff_filename)

        # Filter essentiality data for the current strain
        strain_df = essentiality_df[essentiality_df["locus_tag"].str.startswith(strain)]

        # Create the essentiality GFF3 DataFrame
        gff_df = create_essentiality_gff(strain_df, seqid_mapping)

        # Save the essentiality GFF3 file
        output_filename = f"{strain}_essentiality.gff3"
        gff3_header = "##gff-version 3\n"
        gff_df.to_csv(
            output_filename, sep="\t", index=False, header=False, quoting=3, mode="w"
        )

        # Add the GFF3 header
        with open(output_filename, "r+") as file:
            content = file.read()
            file.seek(0)
            file.write(gff3_header + content)

        print(f"GFF3 file generated: {output_filename}")

    finally:
        # Delete the downloaded GFF file
        if os.path.exists(gff_filename):
            os.remove(gff_filename)
            print(f"Deleted: {gff_filename}")
