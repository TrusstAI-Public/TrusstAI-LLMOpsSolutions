FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12

# Copy requirements.txt and function code
COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY lambda.py ${LAMBDA_TASK_ROOT}

# install dependencies
RUN pip3 install --no-cache-dir -r ./requirements.txt

# Set the CMD to your handler
CMD [ "lambda.lambda_handler" ]
