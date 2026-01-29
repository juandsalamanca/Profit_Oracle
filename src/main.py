from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import tempfile
import base64
import os
import asyncio
import pandas as pd
import json
from fastapi.concurrency import run_in_threadpool
from src.graph import run_graph
from src.s3_retrieval import get_client_snapshot
from src.supabase_functions import download_and_process_files, save_report_in_supabase
from dotenv import load_dotenv
from typing import Optional
import traceback

load_dotenv()

app = FastAPI(title="Profit Oracle API", description="API for processing analysis requests")

def save_data_file(file_content, file_name):

    suffix = file_name.split(".")[-1] if "." in file_name else "tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(file_content)
        temp_path = tmp.name

    return temp_path

def run_analysis(data, client_name=None, snapshot_idx=None):

    # Placeholder for the actual analysis logic
    temp_path = None
    try:
        if data is not None:
            # Read file content
            request_id = data.request_id
            goal = data.goal
            business_profile = data.business_profile
            file_urls = data.file_urls
            print(f"Goal: {goal}, Business Profile: {business_profile}, File URLs: {file_urls}")
            processed_files = download_and_process_files(file_urls)
            file_path_list = []
            for file_info in processed_files:
                file_name = file_info["filename"]
                file_bytes = file_info["content"] if file_info["content"] else b""
                temp_path =  save_data_file(file_bytes, file_name)
                file_path_list.append(temp_path)
        elif client_name and snapshot_idx:
            snapshot = get_client_snapshot(client_name, snapshot_idx)
            for table in snapshot.get("tables", []):
                table_content = snapshot["tables"][table]
                df = pd.DataFrame(table_content)
                file_path = f"{table}.csv"
                df.to_csv(file_path, index=False)
                file_path_list.append(file_path)

        graph_input = {"goal":goal,
                "business_profile":business_profile,
                "data_path":temp_path}

        report, image_path, impact_value = run_graph(graph_input)
        print("Graph done")

        # Save report in Supabase
        if request_id:
            save_report_in_supabase(request_id, report, impact_value)
        # Read and encode the image file as base64
        responses_dir = "responses"
        os.makedirs(responses_dir, exist_ok=True)
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            # Get image file extension for proper MIME type
            image_ext = image_path.split(".")[-1].lower()
            mime_type = f"image/{image_ext}" if image_ext in ['png', 'jpg', 'jpeg', 'gif', 'svg'] else "image/png"

            result = {
            "report": report,
            "impact_value": impact_value,
            "image": {
                "data": image_data,
                "mime_type": mime_type,
                "filename": os.path.basename(image_path)
            },
            "status": "success"
            }

            with open(os.path.join(responses_dir, f"{request_id}_response.json"), "w") as json_file:
                json.dump(result, json_file)

            print("JSON response built and saved locally")

        except Exception as e:
            traceback.print_exc()
            result = {
            "report": report,
            "impact_value": impact_value,
            "status": "success"
            }
            with open(os.path.join(responses_dir, f"{request_id}_response.json"), "w") as json_file:
                json.dump(result, json_file)

    except Exception as e:
        print(f"Failed to process request: {str(e)}")
        traceback.print_exc()
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

"""
Old code:
goal: str = Form(..., description="The goal/objective of the data analysis process (e.g. increase revenue, etc)"),
    business_profile: str = Form(..., description="Any useful info about the business for the analysis (location, size, industry, important clients, etc)"),
    file_urls: Optional[list[str]] = File([], description="Supabase URLs of the files to be analyzed. This one is only used when the user uploads files through the Kixik platform"),
    file: Optional[UploadFile] = File(None, description="Data file to be analyzed, if the S3 bucket is not used (only csv supported for now)"),
    client_name: Optional[str] = Form("", description="Client ID used in the Sync app to upload data to S3"),
    snapshot_idx: Optional[str] = Form("", description="The index of the snapshot of the data you want. Use -1 for the last one, -2 for second to last, 0 for the first one, 1 for the second, etc."),
    background_tasks: BackgroundTasks = None

    if file is not None:
        file_content = await file.read()
        file_name = file.filename
    else:
        file_content = None
        file_name = None
    background_tasks.add_task(run_analysis, goal, business_profile, file_urls, file_content, file_name, client_name, snapshot_idx)
"""


class AnalysisRequest(BaseModel):
    request_id: str
    goal: str
    business_profile: str
    file_urls: Optional[List[str]] = []


@app.post("/analyze")
async def analyze_data(data: AnalysisRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_analysis, data)
    return JSONResponse(content={"message": "Processing"}, status_code=200)
    
    
    

@app.post("/retrieve_s3")
async def retreive_s3(
    client:str = Form(..., description="Client ID used in the sync app to upload the data"), 
    idx:int = Form(..., description="The index of the snapshot of the data you want. Use -1 for the last one, -2 for second to last, 0 for the first one, 1 for the second, etc.")):

    snapshot = await run_in_threadpool(get_client_snapshot, client, idx)
    return {"snapshot": snapshot}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Profit Oracle API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)

