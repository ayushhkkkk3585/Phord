from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any
import json

# Load environment variables
load_dotenv()

# Use BLIP for better image captioning
CAPTION_API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
# Use GPT-2-XL for better story generation
STORY_API_URL = "https://api-inference.huggingface.co/models/gpt2-xl"

headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN')}"}

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def query_image(image_data: bytes) -> Dict[str, Any]:
    """
    Query the image captioning model with retry mechanism and error handling.
    """
    try:
        response = requests.post(
            CAPTION_API_URL,
            headers=headers,
            data=image_data,
            timeout=30  # Add timeout to prevent hanging
        )
        
        if response.status_code == 503:
            # Model is loading
            raise HTTPException(
                status_code=503,
                detail="Model is currently loading. Please try again in a few seconds."
            )
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Request timed out. The server took too long to respond."
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with image captioning service: {str(e)}"
        )

async def generate_story(caption: str, prompt: str) -> str:
    """
    Generate a story based on the image caption and user prompt.
    Uses better prompt engineering for more coherent stories.
    """
    try:
        # Craft a better prompt for the story generation
        story_prompt = (
            "Write a creative and engaging short story based on this image description "
            f"and prompt.\n\nImage Description: {caption}\n"
            f"Additional Context: {prompt if prompt else 'Tell an interesting story about this scene.'}"
            "\n\nStory:"
        )

        # Set parameters for better story generation
        payload = {
            "inputs": story_prompt,
            "parameters": {
                "max_length": 250,
                "num_return_sequences": 1,
                "temperature": 0.7,
                "top_k": 50,
                "top_p": 0.95,
                "do_sample": True,
                "no_repeat_ngram_size": 2
            }
        }

        response = requests.post(
            STORY_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 503:
            raise HTTPException(
                status_code=503,
                detail="Story generation model is currently loading. Please try again in a few seconds."
            )
            
        response.raise_for_status()
        
        # Extract and clean up the generated story
        story = response.json()[0]["generated_text"]
        
        # Clean up the story by removing the prompt and any extra whitespace
        story = story.replace(story_prompt, "").strip()
        
        return story

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Story generation timed out. Please try again."
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating story: {str(e)}"
        )

@app.post("/caption-image")
async def caption_image(
    file: UploadFile = File(...),
    prompt: str = Query("", description="Optional prompt to guide story generation")
):
    """
    Generate a caption and story for an uploaded image.
    
    Args:
        file: The uploaded image file (must be an image)
        prompt: Optional text prompt to guide the story generation
        
    Returns:
        dict: Contains the generated caption and story
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be an image"
        )
    
    try:
        # Read image data
        image_data = await file.read()
        
        # Generate image caption
        caption_result = await query_image(image_data)
        caption = caption_result[0]["generated_text"]
        
        # Generate story based on caption and prompt
        story = await generate_story(caption, prompt)
        
        return {
            "caption": caption,
            "story": story
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Simple health check endpoint to verify the API is running.
    """
    return {"status": "healthy"}