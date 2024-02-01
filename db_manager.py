# db_manager.py
# This module manages the database operations for the SQL Playground app.
# It includes functions to execute SQL queries.

import sqlite3
import os
from typing import Any

from eralchemy2 import render_er


def sql_executor(raw_code: str, db_name: str) -> tuple[list[Any], list[Any]] | tuple[list[Any], str] | str:
    """
    Execute SQL queries and return results or confirmation messages.

    For SELECT queries, it returns a list of tuples representing the rows fetched
    and a list of column names. For DML and DDL statements, it returns a
    confirmation message.

    Parameters:
    raw_code (str): SQL query or multiple queries separated by semicolons.
    db_name (str): Name of the database file to connect to.

    Returns:
    Union[Tuple[List, List], str]: Results for each SELECT query executed or
                             confirmation for non-SELECT queries.
    """
    conn = sqlite3.connect(os.path.join('data', db_name))
    c = conn.cursor()
    try:
        # Split the input by semicolons to separate individual SQL statements
        statements = raw_code.strip().split(';')

        # Process each statement
        for statement in statements:
            # Skip any empty statements
            if not statement.strip():
                continue

            # Execute the statement
            c.execute(statement.strip())

            # If it's a SELECT statement, fetch results
            if statement.strip().upper().startswith(('SELECT', 'WITH')):
                column_names = [desc[0] for desc in c.description]
                data = c.fetchall()
                return data, column_names

        # Commit for non-SELECT statements
        conn.commit()
        return [], "Executed non-SELECT statement."

    except sqlite3.OperationalError as e:
        conn.rollback()
        return [], f"SQL Error: {e}"
    except Exception as e:
        conn.rollback()  # Ensure the data is properly rollback
        return [], f"An error occurred: {e}"
    finally:
        conn.close()  # Ensure the connection is always closed


def generate_er_diagram(database_path: str, selected_db: str) -> str:
    """
    Generate an Entity-Relationship diagram for a SQLite database.

    This function creates an ER diagram and saves it as a PNG file
    in the specified output directory. It uses ERAlchemy to render
    the diagram based on the database schema.

    Parameters:
    - database_path (str): The path to the SQLite database file.
    - selected_db (str): The name of the selected database.

    Returns:
    - str: The file path to the saved ER diagram image.
    """

    # Define the output path for the ER diagram
    output_path: str = f'./er_diagram/{selected_db}.png'

    # Create the output directory if it does not exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate the ER diagram using ERAlchemy
    render_er(f'sqlite:///{database_path}', output_path)

    # Return the output path of the generated ER diagram
    return output_path
