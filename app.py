import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from openai import OpenAI
import io
from PyPDF2 import PdfReader
import tabula


from pathlib import Path
import tempfile
import json

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # Store key in secrets


def analyze_data(df, query):
    prompt = f"""
    DataFrame columns: {', '.join(df.columns)}
    Data preview: {df.head().to_string()}
    Query: {query}
    
    Respond with executable Python code that:
    1. Uses the 'df' DataFrame
    2. Uses matplotlib, seaborn, or plotly for visualizations
    3. Stores any calculated results in 'result' variable
    4. Includes axis labels and titles for plots
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a data visualization expert. Provide executable Python code that creates clear, informative visualizations or calculations."},
            {"role": "user", "content": prompt}
        ]
    )
    
    try:
        code = response.choices[0].message.content.strip()
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0]
        
        # Setup visualization environment
        local_vars = {
            'df': df,
            'plt': plt,
            'pd': pd,
            'sns': sns,
            'np': np
        }
        
        # Execute the analysis code
        exec(code, globals(), local_vars)
        
        # Show results if any
        if 'result' in local_vars:
            st.write("Analysis Result:", local_vars['result'])
        
        # Display any plots
        if plt.get_fignums():
            st.pyplot(plt)
            plt.clf()
            
    except Exception as e:
        st.error(f"Visualization error: {str(e)}")

def read_pdf(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_path = tmp_file.name

    try:
        tables = tabula.read_pdf(tmp_path, pages='all', multiple_tables=True)


        if tables:
            return pd.concat(tables, ignore_index=True)
        
        pdf = PdfReader(tmp_path)
        text = []
        for page in pdf.pages:
            text.append(page.extract_text())
        return pd.DataFrame({"page_number": range(1, len(text) + 1), "text": text})
    
    finally:
        Path(tmp_path).unlink()
def read_file(file):
    file_type = file.type
    try:
        if file_type == "text/csv":
            return pd.read_csv(file)
        elif file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
            return pd.read_excel(file)
        elif file_type == "application/pdf":
            return read_pdf(file)
        else:
            st.error(f"Unsupported file type: {file_type}")
            return None
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None


def main():
    st.set_page_config(page_title=" SAFARI Data Analysis Assistant", page_icon="📊", layout="wide")
    
    # Centered Layout with Styled Logo
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 750px;
            margin: auto;
            padding-top: 30px;
            text-align: center;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        body {
            background-color: #f4f4f4;
        }
        .stTextInput, .stButton {
            width: 80%;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Add logo within styled container
    logo_path = "https://safari.ma/img/logo-1707950070.jpg"
    if Path(logo_path).exists():
        st.image(logo_path, width=120)
    
    # Chat Interface
    st.title(" SAFARI Data Analysis Assistant")
    st.write("Upload your data file and ask questions!")
    
    uploaded_file = st.file_uploader("Upload file (CSV, Excel, PDF)", type=["csv", "xlsx", "pdf"])
    
    if uploaded_file:
        with st.spinner("Reading file..."):
            df = read_file(uploaded_file)
        
        if df is not None:
            st.write("Data Preview:")
            st.dataframe(df.head())
            
            with st.expander("Show data info"):
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())
            
            query = st.text_input("ASK QUESTION ?")
            if query:
                with st.spinner("Analyzing..."):
                    analyze_data(df, query)
    
if __name__ == "__main__":
    main()
