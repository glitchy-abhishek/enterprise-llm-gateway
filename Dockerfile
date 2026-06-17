# 1. Start with a lightweight Linux/Python foundation
FROM python:3.11-slim

# 2. Create a working directory inside the container
WORKDIR /app

# 3. Copy only the requirements first (this makes future builds super fast)
COPY requirements.txt .

# 4. Install the Python packages globally inside the container
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your actual code into the container
COPY . .

# 6. Expose port 8000 so outside traffic can reach it
EXPOSE 8000

# 7. The exact command to boot the server when the container starts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]