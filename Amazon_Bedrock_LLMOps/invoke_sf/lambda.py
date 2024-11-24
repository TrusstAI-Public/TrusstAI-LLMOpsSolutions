import json
import os
import uuid
import boto3

# Initialize the Step Functions client
stepfunctions_client = boto3.client("stepfunctions")


def lambda_handler(event, _context):
    print("Received event:", json.dumps(event, indent=2))
    STEP_FUNCTION_ARN = os.environ["STEPFUNCTION_ARN"]
    try:
        # Log the incoming event for debugging
        print("Received event:", json.dumps(event, indent=2))
        
        # Extract the bucket name and object key from the S3 event
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            file_name = record['s3']['object']['key']
            id= uuid.uuid4()
            # Create input for Step Function
            step_function_input = {
                "TrainingDataBucket": bucket_name,
                "TrainingDataFileName": file_name,
                "BaseModelIdentifier": "cohere.command-light-text-v14:7:4k",
                "CustomModelName": f"custom-model-{id}",
                "JobName": f"custom-job-{id}",
                "HyperParameters": {
                    "evalPercentage": "20.0",
                    "epochCount": "1",
                    "batchSize": "8",
                    "earlyStoppingPatience": "6",
                    "earlyStoppingThreshold": "0.01",
                    "learningRate": "0.00001"
                }
            }
            
            # Start the Step Function
            response = stepfunctions_client.start_execution(
                stateMachineArn=STEP_FUNCTION_ARN,
                input=json.dumps(step_function_input)
            )
            
            # Log the Step Function execution details
            print("Step Function invoked successfully:", response)
        
        return {
            "statusCode": 200,
            "body": json.dumps("Step Function invoked successfully.")
        }
    
    except Exception as e:
        print(f"Error invoking Step Function: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error invoking Step Function: {str(e)}")
        }
