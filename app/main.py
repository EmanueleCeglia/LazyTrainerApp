from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
import os


# Set up your OpenAI API key, ensuring you have it available as environment variable.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create the FastAPI app instance
app = FastAPI()

# Define the data model for the incoming JSON payload
class RequestData(BaseModel):
    nome: str      # The user's name
    prompt: str    # The prompt provided by the user



# Define the endpoint that receives the JSON data from the Android app
@app.post("/sendprompt")
async def process_request(data: RequestData):
    try:
        # Create a new prompt by combining the 'nome' and 'prompt' received
        new_prompt = f"User name: {data.nome}. Please process the following prompt: {data.prompt}"
        
        # Call the GPT API using OpenAI's Completion API
        response = client.responses.create(
            model="gpt-4o-mini",
            input=new_prompt
        )
        
        # Estrai la risposta (testo generato) dalla risposta dell'API
        generated_text = response.output_text
        
        # Restituisci la risposta in formato JSON
        return JSONResponse(content={"generated_text": generated_text}, headers={"Content-Type": "application/json; charset=utf-8"})
    
    except Exception as e:
        # In caso di errori, restituisci uno status 500 e il messaggio d'errore
        raise HTTPException(status_code=500, detail=str(e))


