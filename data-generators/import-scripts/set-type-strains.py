import psycopg

# Database connection setup
conn = psycopg.connect(
    dbname="postgres",
    user="postgres",
    password="pass123",
    host="localhost",
    port="5432",
)

# Define the isolate names that should be updated
isolate_names = ["BU_ATCC8492", "PV_ATCC8482"]

# Define the update query
update_query = """
UPDATE strain
SET type_strain = TRUE
WHERE isolate_name = %s;
"""

# Update data in the Strain table
with conn.cursor() as cursor:
    for isolate in isolate_names:
        cursor.execute(update_query, (isolate,))
    conn.commit()

print("Successfully updated type strain flags for the specified isolates.")

# Close the connection
conn.close()
