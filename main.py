import streamlit as st
import tempfile
from src.graph import run_graph
from dotenv import load_dotenv
load_dotenv()

st.header("Profit Oracle Agents")

business_profile = st.text_input("Input here your business profile")

goal = st.text_input("Input here your goal with our services")

input_file = st.file_uploader("Upload the payroll register file")

if input_file is not None:
    suffix = input_file.name.split(".")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(input_file.getbuffer())
        temp_path = tmp.name

graph_input = {"goal":goal,
              "business_profile":business_profile,
              "data_path":temp_path}


report, image_path = run_graph(graph_input)

st.image(image_path)
st.write(report)

