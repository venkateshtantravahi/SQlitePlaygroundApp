# main.py
# This script is the main application file for the Streamlit SQL Playground app.
# It handles the user interface and user interactions.

import pandas as pd
import streamlit as st
import sqlparse
import os
from streamlit.components.v1 import iframe

from helper import (process_uploaded_files, list_database_schema,
                    list_databases, handle_create_database_query, encode_image)
from db_manager import sql_executor, generate_er_diagram


def main():
    """
    Main function to run the Streamlit app.
    """
    st.set_page_config(layout='wide')
    st.title("SQLite Playground")

    menu = ['Home', 'About', 'SQL Documentation']
    choice = st.sidebar.selectbox('Menu', menu, index=menu.index('About'))
    # Ask the user if all files belong to the same database
    same_db = st.sidebar.radio("Do all files belong to the same database?", ("Yes", "No"))
    upload_files = st.sidebar.file_uploader("Upload your Data or Database file", type=['xlsx', 'csv', 'sqlite'],
                                            accept_multiple_files=True)

    if upload_files is not None and len(upload_files) > 0:
        process_uploaded_files(upload_files, same_db)

    if choice == 'Home':
        st.subheader("Editor Playground")
        db_files = list_databases()
        selected_db = st.selectbox("Select Database", db_files)
        with st.spinner("Generating ER Diagram..."):
            diagram_path = os.path.join('er_diagram', f'{selected_db}.png')
            if not os.path.exists(diagram_path):
                diagram = generate_er_diagram(os.path.join('data', f'{selected_db}.sqlite'), selected_db)
            else:
                diagram = diagram_path
        with st.expander("ER Diagram", expanded=True):
            st.image(diagram, use_column_width=True)
        home_page(selected_db)
    elif choice == 'About':
        about_page(choice)
    elif choice == 'SQL Documentation':
        documentation_page()


def documentation_page():
    with open('SQL Documentation/SQL Cheat Sheet.md', 'r') as file:
        markdown_content = file.read()
    st.markdown(markdown_content)


def about_page(choice):
    st.subheader("About SQL Playground")
    st.markdown('''
    # SQLite Playground Documentation

    Welcome to the SQLite Playground, a versatile platform for managing and 
    exploring SQLite databases. This tool is designed to accommodate both novice 
    users and seasoned database professionals.
    
    ## Comprehensive Features
    
    ### Advanced SQL Editor
    Write and execute SQL queries efficiently with features like:
    - Syntax Highlighting
    - Error Detection
    ''', unsafe_allow_html=True)
    st.image(encode_image('static/img.png'))
    st.markdown('''
    ### Database Management
    Easily manage your SQLite databases:
    - Create, delete, and modify databases using queries
    - Manage database schemas to which you want to work with using a dropdown list.
    ''')
    st.image(encode_image('static/img_1.png'))
    st.markdown('''
    ### SQL Script Upload and Execution
    Automate tasks with batch processing:
    - Upload and execute `.sql` scripts
    - Convenient for repetitive database operations
    ''')
    st.image(encode_image('static/img_2.png'))
    st.markdown('''
    ### Schema Visualization
    Understand and optimize your database structure:
    - Visualize database schemas
    - Explore table relationships
    ''')
    st.image(encode_image('static/img_3.png'))
    st.markdown('''
    ### Data Table Visualization
    View query results in a user-friendly format:
    - Enhanced data readability
    - Table format for easier analysis
    ''')
    st.image(encode_image('static/img_4.png'))
    st.markdown('''
    ### File Uploader
    Seamlessly integrate data:
    - Upload `.csv`, `.xls`, `.xlsx`, or `.sqlite` files
    - Create and populate databases from various file formats
    ''')
    st.image(encode_image('static/img_5.png'))
    st.markdown("Its common to struck in between writing "
                "queries if you are so then refer the sql cheat "
                "sheet attached in the SQL Documentation menu item.")
    st.markdown('''
    ## Developer Information
    For inquiries or support, contact Venkatesh Tantravahi at [vtantravahi@gmail.com](mailto:vtantravahi@gmail.com).
    
    ## Feedback
    We appreciate your feedback! Share your thoughts and suggestions.
    
    ---
    
    SQLite Playground - Enhance your data management and SQL skills.
    ''')
    with st.expander('Feedback Form'):
        iframe(src="https://docs.google.com/forms/d/e/1FAIpQLSebdFz74Bt8MGLC0SDo-"
                   "-HfMZGz_d-JNtRFUee75Mg73B-sTw/viewform?embedded=true",
               scrolling=True, height=750, width=640)


def home_page(selected_db):
    """
    Home page of the application, displaying the query interface and results.
    """
    col1, col2 = st.columns(2)

    with col1:
        with st.form(key='query_form'):
            sql_script = st.file_uploader("Upload your SQL Scripts", type=['sql'], accept_multiple_files=True)
            raw_code = ""
            if sql_script is not None and len(sql_script) > 0:
                script = sql_script[0].getvalue().decode('utf-8')
                # Format the script using sqlparse and set it as the default value for the text area
                raw_code = sqlparse.format(script, reindent=True, keyword_case='upper')

            raw_code = sqlparse.format(st.text_area("Query Here", value=raw_code), reindent=True, keyword_case='upper')
            # check for the error that form submit button is missing
            submit_code = st.form_submit_button("Execute")

        with st.expander("Schema Information"):
            schema_info = list_database_schema(selected_db)
            st.json(schema_info)

    with col2:
        if submit_code:
            st.info("Query Submitted")
            if raw_code.strip() == "":  # Check if the query is empty
                st.info("Please input your query to execute and refer to the table columns below in Table Info.")
            elif handle_create_database_query(raw_code):
                st.success("Database created successfully.")
            else:
                st.code(raw_code, language='sql')
                query_results, column_names = sql_executor(raw_code, f'{selected_db}.sqlite')
                if isinstance(query_results, list):
                    # Query executed successfully, display results
                    if column_names:
                        with st.expander('Results'):
                            st.write(query_results)

                        with st.expander("Pretty Table Format"):
                            if len(query_results) > 0 and not None:
                                query_df = pd.DataFrame(query_results, columns=column_names)
                                st.dataframe(query_df)
                            else:
                                st.error("Please Make sure the query is correct.")

                    else:
                        st.info(query_results)
                else:
                    # There was an error, display the error message
                    st.error(query_results)


if __name__ == "__main__":
    main()
