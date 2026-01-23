from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uvicorn
import tempfile
import base64
import os
from src.graph import run_graph
from src.s3_retrieval import get_last_client_snapshot
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Profit Oracle API", description="API for processing analysis requests")


@app.post("/analyze")
async def analyze_data(
    goal: str = Form(..., description="First string parameter"),
    business_profile: str = Form(..., description="Second string parameter"),
    file: UploadFile = File(..., description="File to analyze")
    ):
    
    temp_path = None
    try:
        # Read file content
        file_content = await file.read()
        suffix = file.filename.split(".")[-1] if "." in file.filename else "tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(file_content)
            temp_path = tmp.name

        graph_input = {"goal":goal,
                "business_profile":business_profile,
                "data_path":temp_path}

        report, image_path = run_graph(graph_input)
        print("Graph done")
        # Read and encode the image file as base64
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            print("image encoded")
            # Get image file extension for proper MIME type
            image_ext = image_path.split(".")[-1].lower()
            mime_type = f"image/{image_ext}" if image_ext in ['png', 'jpg', 'jpeg', 'gif', 'svg'] else "image/png"
            print("mime", mime_type)
            print(image_path)
            result = {
            "report": report,
            "image": {
                "data": image_data,
                "mime_type": mime_type,
                "filename": os.path.basename(image_path)
            },
            "status": "success"
            }
            print("JSON response built")

        except Exception as e:
            print(e)
            result = {
            "report": report,
            "status": "success"
            }

        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to process request: {str(e)}"},
            status_code=500
        )
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

@app.post("/retrieve_s3")
async def retreive_s3(client:str = Form(...), idx:int = Form(...)):

    snapshot = get_last_client_snapshot(client, idx)
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

