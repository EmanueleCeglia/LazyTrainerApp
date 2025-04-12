FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# To build the Docker image, run the following command in the terminal:
# docker build -t myfastapiapp .
# To run the Docker container, use the following command:
# docker run -d -p 8000:8000 myfastapiapp
# You can then access the FastAPI application at http://localhost:8000
# To stop the container, use the following command:
# docker ps -a (to find the container ID)
# docker stop <container_id>
