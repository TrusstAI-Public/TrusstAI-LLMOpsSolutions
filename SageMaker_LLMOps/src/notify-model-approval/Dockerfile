FROM --platform=linux/arm64 public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}
COPY requirements.txt .
COPY lambda.py .

# install dependencies
RUN pip3 install --no-cache-dir -r ./requirements.txt
# Set the CMD to your handler
CMD [ "lambda.lambda_handler" ]
