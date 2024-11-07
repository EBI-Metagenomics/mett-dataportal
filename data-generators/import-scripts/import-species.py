import pandas as pd
import psycopg

# Database connection setup
conn = psycopg.connect(
    dbname="postgres",
    user="postgres",
    password="pass123",
    host="localhost",
    port="5432",
)

# Load the CSV file into a DataFrame
species_df = pd.read_csv("species.csv")
print(f"Species DataFrame: \n{species_df}")

# Define insert query
insert_query = """
INSERT INTO Species (id, scientific_name, common_name, acronym, taxonomy_id)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (taxonomy_id) DO NOTHING; 
"""

# Insert data into Species table
with conn.cursor() as cursor:
    for row in species_df.itertuples(index=False):
        cursor.execute(
            insert_query,
            (
                row.id,
                row.scientific_name,
                row.common_name,
                row.acronym,
                row.taxonomy_id,
            ),
        )
    conn.commit()

print("Species data successfully inserted into the database.")

# Close the connection
conn.close()
