
# Environment Vairable creation
create a .env file in the root with following values
1. Go to Root Folder of travelease
```
API_MODE=huggingface  # or 'bedrock' for production
# This is for solving SSL Errors because of VPN
REQUESTS_CA_BUNDLE =/Users/{UNAME}/cert/bundle.pem
# HuggingFace credentials
HF_EMAIL=uname@maildomain.com
HF_PASS=yourpassword

# AWS credentials (for Bedrock)
AWS_REGION=your_aws_region
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

USE_GOOGLE_MAPS=True  # Set to True in production
GOOGLE_MAPS_API_KEY=your_api_key
# Anthropic Key
ANTHROPIC_API_KEY=your_api_key
```
# Install dependencies
2. Go to travelease root forlder
```
pip install -r /path/to/requirements.txt 
streamlit run app.py
```




