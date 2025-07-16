import sqlite3
import io


def test_sql_file(filename):
    # Vytvoření databáze v paměti
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Načtení SQL souboru
    with open(filename, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # Spuštění skriptu
    try:
        cursor.executescript(sql_script)
        print("SQL soubor byl úspěšně načten.")

        # Získání seznamu tabulek
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print("\nTabulky v databázi:")
        for table in tables:
            print(f" - {table[0]}")

            # Získání struktury tabulky
            cursor.execute(f"PRAGMA table_info({table[0]});")
            columns = cursor.fetchall()
            print("   Sloupce:")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")

            # Ukázka dat (prvních 5 řádků)
            cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5;")
            rows = cursor.fetchall()
            if rows:
                print("   Ukázka dat:")
                for row in rows:
                    print("   ", row)
            print()

    except sqlite3.Error as e:
        print(f"Chyba při čtení SQL souboru: {e}")
    finally:
        conn.close()


# Použití
test_sql_file('testdb.sql')