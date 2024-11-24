import boto3
import os
import json
from botocore.exceptions import ClientError
from bert_score import score
import urllib.parse

s3 = boto3.client('s3')
ses = boto3.client('ses')

def get_inferences(bucket, key):
    return json.loads(s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8'))

def compute_bert_score(hypotheses, references):
    P, R, F1 = score(hypotheses, references, model_type="distilbert-base-uncased")
    return P.mean().item(), R.mean().item(), F1.mean().item()  

def send_email(subject, body):
    try:
        response = ses.send_email(
            Source=os.environ['SENDER_EMAIL'],
            Destination={
                'ToAddresses': [os.environ['RECIPIENT_EMAIL']]
            },
            Message={
                'Subject': {'Data': subject},
                'Body': {'Html': {'Data': body,'Charset': 'UTF-8'},
                         'Text': {'Data': body.replace('<[^>]*>', ''),'Charset': 'UTF-8'}}
            }
        )
        return response
    except ClientError as e:
        print(e)
        raise Exception("Error sending email")
        
def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))
    modelId = event.get('input', {}).get('ProvisionedModelArn', None)
    
    reference_hypotheses = get_inferences(os.environ['S3_BUCKET_VALIDATION'], os.environ['REFERENCE_INFERENCE']) 
    base_model_hypotheses = get_inferences(os.environ['S3_BUCKET_INFERENCE'], os.environ['BASE_MODEL_INFERENCE'])
    custom_model_hypotheses = get_inferences(os.environ['S3_BUCKET_INFERENCE'], os.environ['CUSTOM_MODEL_INFERENCE'])
    api_url = os.environ['API_GATEWAY_URL']
    print("api_url:", api_url)
    print("ModelId:", modelId)
    
    if not modelId:
        raise ValueError("ModelId is required but was not provided in the event")
        
    base_F1 = compute_bert_score(base_model_hypotheses, reference_hypotheses)
    custom_F1 = compute_bert_score(custom_model_hypotheses, reference_hypotheses)

    if custom_F1 > base_F1:
        delete_provisioned_throughput = False
        subject = "Amazon Bedrock model customization completed!"
        body = generate_success_email_body(base_F1, custom_F1, model_id=modelId, api_url=api_url)
    else:
        delete_provisioned_throughput = True
        subject = "Amazon Bedrock model customization completed!" 
        body = generate_failure_email_body(base_F1, custom_F1)

    send_email(subject, body)
        
    return {
        'statusCode': 200,
        'deleteProvisionedThroughput': delete_provisioned_throughput
    }

def generate_success_email_body(base_F1, custom_F1, model_id, api_url):
    api_url = api_url.rstrip('/')
    base_f1_formatted = f"{base_F1[2]:.4f}"
    custom_f1_formatted = f"{custom_F1[2]:.4f}"
    # TODO: maybe this formatting is messing up with the model url
    encoded_model_id = urllib.parse.quote(model_id, safe='')
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* Button Styling */
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                text-align: center;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
        </style>
    </head>
    <body>
        <p>Dear LLMOps Engineer,</p>
        <p>We are pleased to inform you that the Amazon Bedrock model customization process has been successfully completed. Based on the evaluation data, the customized model has achieved superior performance compared to the base model. Here are the results:</p>
        <ul>
            <li><b>Base model average F1:</b> {base_f1_formatted}</li>
            <li><b>Custom model average F1:</b> {custom_f1_formatted}</li>
        </ul>
        <p>If you wish to approve the deployment of the customized model, please click the button below:</p>
        <p>
            <a href="{api_url}/updateModelArn/{encoded_model_id}" class="button">Approve Custom Model</a>
        </p>
        <p>Sincerely, <br>The LLM Service Team</p>
    </body>
    </html>
    """

def generate_failure_email_body(base_F1, custom_F1):
    return f"Dear LLMOps Engineer, \n\n Amazon Bedrock model customization has been completed. Based on the validation data the customized model underperformed the base model. Please customize the base model again by changing training data or hyper-parameters. Please note the evaluation outcome: \n\n Base model average F1: {base_F1} \n\n Custom model average F1: {custom_F1}  \n\n Sincerely, \nThe LLM Service Team."
