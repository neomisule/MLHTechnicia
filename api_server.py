"""
FastAPI server to handle requests from the React frontend.
"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import asyncio
from pathlib import Path
from runner import runner

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/analyze")
async def analyze(
    question: str = Form(...),
    model: str = Form(...),
    agent: str = Form("general_agent"),
    images: list[UploadFile] = File(None)
):
    """
    Endpoint to analyze images with a question (images are optional).
    """
    try:
        # Handle image upload if provided
        image_input = None
        temp_image_paths = []
        
        if images and len(images) > 0:
            # Save uploaded images to temporary files
            for image in images:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{image.filename}") as tmp_file:
                    content = await image.read()
                    tmp_file.write(content)
                    temp_image_paths.append(tmp_file.name)
            
            # Set image_input based on number of images
            image_input = temp_image_paths if len(temp_image_paths) > 1 else temp_image_paths[0]
        
        # Run the analysis with the selected model and agent
        result = await runner(question, image_input, model, agent)
        
        # Clean up temporary files
        for path in temp_image_paths:
            try:
                Path(path).unlink()
            except:
                pass
        
        return JSONResponse({
            "result": result,
            "success": True
        })
    
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "success": False
        }, status_code=500)

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

