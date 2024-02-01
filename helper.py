# helper.py
# This module contains helper functions for the SQL Playground app.
import sqlite3
import os


import numpy as np
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from PIL import Image


def list_databases() -> List[str]:
    """
       List all the SQLite database files in the 'data' directory.

       This function scans the 'data' directory for files with a '.sqlite' extension
       and returns their names without the extension.

       Returns:
           List[str]: A list of database names without the '.sqlite' extension.
    """
    # List comprehension to filter and process database files
    return [f.split(".")[0] for f in os.listdir("data") if f.endswith(".sqlite")]


def get_db_schema(db_path: str) -> Dict[str, List[str]]:
    """
        Retrieve the schema of the specified SQLite database.

        This function connects to the SQLite database at the given path and
        constructs a dictionary that maps table names to a list of their column names.

        Parameters:
        - db_path (str): The file path to the SQLite database.

        Returns:
        - Dict[str, List[str]]: A dictionary where each key is a table name and each value is a list of column names.
    """
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Retrieve the list of tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {table[0]: [] for table in cursor.fetchall()}

    # Retrieve the schema for each table
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        # Extract column names from the table info
        tables[table] = [column_info[1] for column_info in cursor.fetchall()]

    # Close the connection to the database
    conn.close()

    return tables


def list_database_schema(selected_db_name: str) -> Dict[str, Any]:
    """
        List the schema of the selected SQLite database.

        Parameters:
        - selected_db_name (str): The name of the selected database.

        Returns:
        - Dict[str, Any]: A dictionary containing the schema of the selected database.
    """
    db_schemas = {}
    db_path = os.path.join("data", f"{selected_db_name}.sqlite")

    # Check if the database file exists and retrieve its schema
    if os.path.exists(db_path):
        db_schemas[selected_db_name] = get_db_schema(db_path)

    return db_schemas


def save_uploaded_file(uploadedfile) -> None:
    """
        Save an uploaded file to the 'data' directory.

        Parameters:
        - uploadedfile: The file uploaded by the user.

        Returns:
        - None
    """
    # Save the file in the 'data' directory
    with open(os.path.join("data", uploadedfile.name), "wb") as f:
        f.write(uploadedfile.getbuffer())

    # Notify the user that the file has been saved
    return st.success("Saved File:{} to Data".format(uploadedfile.name))


def save_dataframe_to_sqlite(df: pd.DataFrame, db_name: str, table_name: str) -> None:
    """
        Save a DataFrame to a SQLite database.

        This function writes a pandas DataFrame to a SQLite database table. If the table
        already exists, it will be replaced.

        Parameters:
        - df (pd.DataFrame): The DataFrame to be saved.
        - db_name (str): The name of the SQLite database file.
        - table_name (str): The name of the table where the DataFrame will be stored.

        Returns:
        - None
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(f"data/{db_name}.sqlite")

    # Write the DataFrame to the specified table
    df.to_sql(name=table_name, con=conn, if_exists="replace", index=False)

    # Close the database connection
    conn.close()


def process_uploaded_files(uploaded_files: List, same_db: bool) -> None:
    """
       Process the uploaded files and save them to a SQLite database.

       Depending on the same_db flag, this function either saves all uploaded files
       to a single SQLite database or creates separate databases for each file.

       Parameters:
       - uploaded_files (List): A list of uploaded files.
       - same_db (bool): Flag indicating whether to save all files to the same database.

       Returns:
       - None
    """
    if same_db:
        # Process files for the same database
        db_name = os.path.splitext(uploaded_files[0].name)[0]
        if '-' in db_name:
            db_name = db_name.replace('-', '_')
        # Process each file and save to the same database
        for uploaded_file in uploaded_files:
            try:
                if uploaded_file.name.endswith((".xls", ".xlsx")):
                    # Handle Excel files
                    xls = pd.ExcelFile(uploaded_file)
                    for sheet_name in xls.sheet_names:
                        if '-' in sheet_name:
                            sheet_name = sheet_name.replace('-', '_')
                        df = pd.read_excel(xls, sheet_name=sheet_name)
                        save_dataframe_to_sqlite(df, db_name, sheet_name)
                elif uploaded_file.name.endswith(".csv"):
                    # Handle CSV files
                    df = pd.read_csv(uploaded_file)
                    table_name = os.path.splitext(uploaded_file.name)[0]
                    if '-' in table_name:
                        table_name = table_name.replace('-', '_')
                    save_dataframe_to_sqlite(df, db_name, table_name)
                elif uploaded_file.name.endswith(".sqlite"):
                    save_uploaded_file(uploaded_file)
                st.success(f"Saved {uploaded_file.name} to {db_name}.sqlite")

            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        # Process files for separate databases
        # Create a separate database for each file
        for uploaded_file in uploaded_files:
            try:
                if uploaded_file.name.endswith(".sqlite"):
                    save_uploaded_file(uploaded_file)
                    st.success(f"Created Database {uploaded_file.name}.sqlite")
                else:
                    db_name = os.path.splitext(uploaded_file.name)[0]
                    if '-' in db_name:
                        db_name = db_name.replace('-', '_')
                    # Read file into DataFrame
                    df = (
                        pd.read_csv(uploaded_file)
                        if not uploaded_file.name.endswith((".xls", ".xlsx"))
                        else pd.read_excel(uploaded_file)
                    )
                    # Save to individual database
                    save_dataframe_to_sqlite(
                        df, db_name, "table_name"
                    )
                    st.success(f"Created database {db_name}.sqlite")
            except Exception as e:
                st.error(f"An error occurred: {e}")


def handle_create_database_query(query: str, databases_dir: str = "data") -> bool:
    """
    Handles a CREATE DATABASE query by creating a new SQLite database file.

    :param query: SQL query string.
    :param databases_dir: Directory to store database files.
    :return: Whether a new database was created.
    """
    if query.lower().startswith("create database"):
        db_name = query.split()[2]  # Assuming the syntax is 'CREATE DATABASE db_name'
        if db_name[-1] == ";":
            db_name = db_name.replace(";", "")
            db_path = os.path.join(databases_dir, f"{db_name}.sqlite")
        else:
            db_path = os.path.join(databases_dir, f"{db_name}.sqlite")

        if not os.path.exists(db_path):
            # Create a new database file
            open(db_path, "w").close()
            return True

    return False


def encode_image(path: str) -> np.array:
    if path is not None:
        image = Image.open(path)
        return np.array(image)
