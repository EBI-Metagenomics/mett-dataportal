import pandas as pd
import requests
import os

# URLs for the FTP server GFF files
ftp_urls = {
    "BU_ATCC8492": "https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/BU_ATCC8492/functional_annotation/merged_gff/BU_ATCC8492_annotations.gff",
    "PV_ATCC8482": "https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/PV_ATCC8482/functional_annotation/merged_gff/PV_ATCC8482_annotations.gff",
}

# Load the essentiality CSV file
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


# Function to parse the GFF file and create a mapping of locus_tag to seqid
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
    gff_df = pd.DataFrame(
        {
            "seqid": df["locus_tag"].map(seqid_mapping),
            "source": "essentiality_analysis",
            "type": "gene",
            "start": df["start"],
            "end": df["end"],
            "score": df["confidence_score_HMM"],  # Use confidence score if available
            "strand": ".",  # Set to '.' if strand is not known
            "phase": ".",
            "attributes": df.apply(
                lambda row: f"ID={row['locus_tag']};Name={row['gene_name']};Essentiality={row['final_essentiality_call_agreement']}_{row['media']};Confidence={row['confidence_score_HMM']}",
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
