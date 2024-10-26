from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx  # Use httpx for async requests
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

CAPTION_API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
STORY_API_URL = "https://api-inference.huggingface.co/models/gpt2-xl"

headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN')}"}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def query_image(image_data: bytes) -> Dict[str, Any]:
    """
    Query the image captioning model asynchronously.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                CAPTION_API_URL,
                headers=headers,
                content=image_data,
                timeout=15  # Reduce timeout if possible
            )

            if response.status_code == 503:
                raise HTTPException(
                    status_code=503,
                    detail="Model is currently loading. Please try again in a few seconds."
                )

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timed out.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Error in image captioning: {str(e)}")

async def generate_story(caption: str, prompt: str) -> str:
    """
    Generate a story based on the caption and user prompt asynchronously.
    """
    story_prompt = (
        f"Write a creative short story.\n\nImage Description: {caption}\n"
        f"Additional Context: {prompt}\n\nStory:"
    )
    payload = {
        "inputs": story_prompt,
        "parameters": {
            "max_length": 200,  # Reduce length for faster response
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.9,
            "do_sample": True,
            "no_repeat_ngram_size": 2
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                STORY_API_URL,
                headers=headers,
                json=payload,
                timeout=15  # Set a reasonable timeout
            )

            if response.status_code == 503:
                raise HTTPException(
                    status_code=503,
                    detail="Story generation model is currently loading. Please try again in a few seconds."
                )

            response.raise_for_status()
            story = response.json()[0]["generated_text"]
            return story.replace(story_prompt, "").strip()

        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Story generation timed out.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=500, detail=f"Error in story generation: {str(e)}")

@app.post("/caption-image")
async def caption_image(
    file: UploadFile = File(...),
    prompt: str = Query("", description="Optional prompt to guide story generation")
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")
    
    image_data = await file.read()
    caption_result = await query_image(image_data)
    caption = caption_result[0]["generated_text"]
    story = await generate_story(caption, prompt)
    
    return {
        "caption": caption,
        "story": story
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
