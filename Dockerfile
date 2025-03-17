FROM python:3.10.7-slim-buster

# Set the working directory
WORKDIR /whatsapptp

# Copy the requirements file
COPY requirements.txt .

# Install necessary dependencies
RUN apt-get update && \
    apt-get -y install tree sudo nano vim git libpq-dev python3-dev gcc ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application code
COPY . .

# Expose the default Cloud Run port
EXPOSE 8080

# Set the PORT environment variable explicitly
ENV PORT=8080


CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
