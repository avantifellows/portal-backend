# Use the official Python 3.9 base image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Set environment variables using the ENV instruction
ENV JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENV DB_SERVICE_URL=${DB_SERVICE_URL}
ENV DB_SERVICE_TOKEN=${DB_SERVICE_TOKEN}

# Define the command to run the FastAPI application using CMD
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
