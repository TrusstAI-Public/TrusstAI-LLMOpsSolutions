import boto3
import os
import json
from botocore.exceptions import ClientError


s3 = boto3.client('s3')
ses = boto3.client('ses')

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
    print(f"Received event: {json.dumps(event)}")
    
    # Extract model details
    detail = event['detail']
    model_package_group_name = detail['ModelPackageGroupName']
    model_package_arn = detail['ModelPackageArn']
    model_package_version = detail['ModelPackageVersion']

    if not model_package_group_name or not model_package_arn:
        raise ValueError("ModelPackageGroupName/ModelPackageArn is required but was not provided in the event")
    # Create approval/reject links
    api_url = os.environ['API_GATEWAY_URL']
    approve_url = f"{api_url}/approve?arn={model_package_arn}&version={model_package_version}"
    reject_url = f"{api_url}/reject?arn={model_package_arn}&version={model_package_version}"
    subject = f"Model Approval Required - {model_package_group_name}"              
    body = generate_email_body(model_package_group_name= model_package_group_name,approve_url=approve_url, reject_url=reject_url)

    send_email(subject, body)
        
    return {
        'statusCode': 200,
        'message': "Email sent successfully"
    }

def generate_email_body(model_package_group_name, approve_url, reject_url):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
<style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .model-info {{
                background-color: #f8f9fa;
                border-left: 4px solid #6a1b9a;
                padding: 15px;
                margin: 20px 0;
            }}
            .button-container {{
                display: flex;
                gap: 20px;  /* Increased gap between buttons */
                margin-top: 30px;
                justify-content: flex-start;
                align-items: center;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 16px;
                text-align: center;
                min-width: 200px;  /* Fixed width for both buttons */
                margin: 0 10px;    /* Added margin on both sides */
            }}
            .approve {{
                background-color: #4CAF50;
                color: white !important;  /* Force white color */
            }}
            .approve:hover {{
                background-color: #45a049;
            }}
            .reject {{
                background-color: #dc3545;
                color: white !important;  /* Force white color */
            }}
            .reject:hover {{
                background-color: #c82333;
            }}
        </style>
    </head>
    <body>
        <h1>Dear LLM Team, a new model requires your approval.</h1>
        
        <p>Amazon Bedrock model customization has been completed and is waiting for your approval.</p>
        
        <div class="model-info">
            <strong>Model Package Group:</strong> {model_package_group_name}
        </div>

        <p>Sincerely,<br>The LLMOps Team</p>

        <div class="button-container">
            <a href="{approve_url}" class="button approve">Approve Custom Model</a>
            <a href="{reject_url}" class="button reject">Reject Custom Model</a>
        </div>
    </body>
    </html>
    """