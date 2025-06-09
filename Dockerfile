# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Run app.py when the container launches
# --server.address=0.0.0.0 is crucial to make it accessible outside the container
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"] 