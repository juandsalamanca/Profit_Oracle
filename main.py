import streamlit as st
import tempfile
from datetime import datetime
from src.graph import run_graph
from dotenv import load_dotenv
load_dotenv()


if "report" not in st.session_state:
    st.session_state.report = None

if "image_path" not in st.session_state:
    st.session_state.image_path = None


st.header("Profit Oracle Agents")

business_profile = st.text_input("Input here your business profile")

goal = st.text_input("Input here your goal with our services")

input_file = st.file_uploader("Upload the payroll register file")

if input_file is not None:
    suffix = input_file.name.split(".")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(input_file.getbuffer())
        temp_path = tmp.name

if business_profile and goal and input_file is not None:
    graph_input = {"goal":goal,
                "business_profile":business_profile,
                "data_path":temp_path}

    process = st.button("Get Report")

    if process:
        start = datetime.now()
        st.session_state.report, st.session_state.image_path = run_graph(graph_input)
        print("Total Latency:", datetime.now()-start)
    if st.session_state.report is not None:
        st.write(st.session_state.report)
        if st.session_state.image_path is not None:
            st.image(st.session_state.image_path)

