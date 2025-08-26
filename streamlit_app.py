import streamlit as st 
import requests 
import pandas as pd 


#---Configuration-----
API_URL = "http://127.0.0.1:8000"   #This is the base URL of our FastAPI backend

st.set_page_config(page_title = "Agentic_AI Recruitment System", layout = "wide")
st.title("Agentic-AI Recruitment System")

#---------Helper Function to Interact with the API------------

def get_from_db(collection_name):
    """ 
        Helper function to fethch all documents from a collection via a potential future endpoint.
    """
    
    return st.session_state.get(collection_name, {})

def display_docs_as_table(collection_name, docs_dict):
    """
        Displays documents in a readable table. 
    """
    if not docs_dict:
        st.info(f"No documents in {collection_name} yet.")
        return
    
    df_data = []
    for doc_id, filename in docs_dict.items():
        df_data.append({"ID": doc_id, "Filename": filename})
    
    st.dataframe(pd.DataFrame(df_data), use_container_width=True)
    
#---------Main App Sections-----------
if 'resumes' not in st.session_state:
    st.session_state['resumes'] = {}
if 'jds' not in st.session_state:
    st.session_state['jds'] = {}

#==============UPLOAD SECTION==============
st.header("1. Upload Documents")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload a Resume")
    uploaded_resume = st.file_uploader(
        "Upload a resume file(PDF, DOCX, JPG/PNG)",
        type = ['pdf', 'docx', 'png', 'jpg'],
        key = "resume_uploader"
    )
    if st.button("Process Resume") and uploaded_resume:
        with st.spinner("Parsing Resume....."):
            files = {'resume_file': (uploaded_resume.name, uploaded_resume.getvalue(), uploaded_resume.type)}
            try:
                response = requests.post(f"{API_URL}/v1/resumes", files = files)
                if response.status_code == 201:
                    resume_id = response.json().get("resume_id")
                    st.session_state.resumes[resume_id] = uploaded_resume.name
                    st.success(f"Resume processed successfully! ID: `{resume_id}`")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            
            except requests.exceptions.ConnectionError:
                st.error("Connection Error: Check the backend server.")

with col2:
    st.subheader("Upload a Job Description")
    uploaded_jd = st.file_uploader(
        "Upload a job description file(.txt)",
        type = ['txt'],
        key = "jd_uploader"
    )
    
    if st.button("Process JD") and uploaded_jd:
        with st.spinner("Parsing JD....."):
            files = {'jd_file': (uploaded_jd.name, uploaded_jd.getvalue())}
            try:
                response = requests.post(f"{API_URL}/v1/jds/upload-file", files = files)
                if response.status_code == 201:
                    jd_id = response.json().get("jd_id")
                    st.session_state.jds[jd_id] = uploaded_jd.name
                    st.success(f"JD processed successfully! ID: `{jd_id}`")
                
                else:
                    st.error(f"Error: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Connection Error: Check the server")
st.divider()

#==============SCREENING SECTION=========================
st.header("2. Screen Candidate")

col3, col4 = st.columns(2)
with col3:
    st.subheader("Available Resumes")
    resumes_in_db = st.session_state.get('resumes', {})
    display_docs_as_table("Resumes", resumes_in_db)

with col4:
    st.subheader("Available Job Descriptions")
    jds_in_db = st.session_state.get('jds', {})
    display_docs_as_table("Job Descriptions", jds_in_db)


if resumes_in_db and jds_in_db:
    with st.form("screening_form"):
        st.write("Select a resume and a JD to screen:")
        selected_resume_id = st.selectbox("Choose a Resume ID", options=list(resumes_in_db.keys()))
        selected_jd_id = st.selectbox("Choose a JD ID", options=list(jds_in_db.keys()))
        
        submitted = st.form_submit_button("Screen Candidate")
        if submitted:
            with st.spinner("Agent is analyzing the match..."):
                payload = {"resume_id": selected_resume_id, "jd_id": selected_jd_id}
                try:
                    screen_response = requests.post(f"{API_URL}/v1/screen", json=payload)
                    
                    if screen_response.status_code == 200:
                        screening_id = screen_response.json().get("screening_id")
                        st.success(f"Screening complete! Fetching report for screening ID: `{screening_id}`")
                    
                        report_response = requests.get(f"{API_URL}/v1/reports/{screening_id}")
                        if report_response.status_code == 200:
                            report_markdown = report_response.json().get("report")
                            st.subheader("Screening Report")
                            st.markdown(report_markdown)
                        else:
                            st.error(f"Could not fetch report: {report_response.status_code} - {report_response.text}")
                    else:
                        st.error(f"Screening failed: {screen_response.status_code} - {screen_response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("Connection Error: Is the backend server running?")    