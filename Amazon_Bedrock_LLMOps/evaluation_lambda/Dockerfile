FROM --platform=linux/arm64 public.ecr.aws/lambda/python:3.12

# Change working directory to Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy only the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies directly into the Lambda task root
RUN pip install --no-cache-dir --target . -r requirements.txt

# Copy application code
COPY app.py .

# Set the CMD to your handler
CMD [ "app.lambda_handler" ]
