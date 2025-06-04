import sqlite3

def drop_table(db_file, table_name):
    try:
        # Connect to the SQLite database file
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Prepare DROP TABLE statement
        sql = f"DROP TABLE IF EXISTS {table_name};"

        # Execute the DROP TABLE command
        cursor.execute(sql)
        conn.commit()

        print(f"Table '{table_name}' dropped successfully (if it existed).")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the connection
        if conn:
            conn.close()

# Example usage
if __name__ == "__main__":
    database_file = "mydatabase.sqlite"  # Path to your SQLite DB file
    table_to_drop = "mytable"            # Table name you want to drop

    drop_table(database_file, table_to_drop)
