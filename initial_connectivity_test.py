# -*- coding: utf-8 -*-
"""
Platform-Independent AWS Bedrock Connectivity Test.

--- USER GUIDE ---

**What is this script for?**
This script is a simple "doctor" for your setup. It checks one thing:
Can your computer successfully connect to Amazon Bedrock using your AWS credentials?

**Why run this first?**
Running this test before the main agent helps you quickly find and fix common setup
problems related to credentials or permissions, saving you time.

**How to Run:**

1.  Make sure you have created and filled out your `.env` file.
2.  Open your terminal or command prompt.
3.  Navigate to this project's directory.
4.  Activate your Python virtual environment.
5.  Run the script:

    `python initial_connectivity_test.py`
"""
# --- Section 0: All Necessary Imports ---
import os
import sys
import traceback
from dotenv import load_dotenv
from strands import Agent

def run_connectivity_test():
    """
    Initializes a basic Strands agent to confirm connectivity with Amazon Bedrock.
    """
    print("--- Securely Configuring AWS Credentials from .env file ---")

    # Load environment variables from your .env file
    load_dotenv()

    # Check that the necessary credentials have been loaded from the .env file.
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION')

    # If any credential is not found, stop and provide clear instructions.
    if not all([aws_access_key, aws_secret_key, aws_region]):
        print("\n--- ❌ ERROR: Missing AWS Credentials ---")
        print("I couldn't find your AWS credentials in the `.env` file.")
        print("Please make sure you have RENAMED `.env.example` to `.env` and filled in your details.")
        sys.exit(1)
        
    print("Credentials and region loaded successfully from .env file.")
    print(f"Attempting to connect to AWS Region: {aws_region}")

    try:
        print("\n--- Initializing Strands Agent (this will contact AWS Bedrock) ---")
        
        # We use a specific model ID. Make sure this model is enabled in your Bedrock console.
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        print(f"Using Model ID: {model_id}")

        agent = Agent(model=model_id)
        print("Agent initialized successfully.")

        print("\n--- Sending a simple test prompt to Bedrock... ---")
        prompt = "Hello, who are you? Respond with a short, one-sentence answer."
        response = agent(prompt)

        print("\n--- Agent Response Received ---")
        print(f'"{response}"')
        print("-------------------------------\n")
        print("✅ Success! Your environment is correctly configured to communicate with Amazon Bedrock.")

    except Exception:
        # If any part of the `try` block fails, this error message will be shown.
        print("\n--- ❌ ERROR: Connectivity Test Failed ---")
        print("An error occurred. Here is a checklist to help you debug:")
        print("1. AWS Credentials: Are the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in your `.env` file EXACTLY correct?")
        print("2. IAM Permissions: Does your IAM user have a policy attached that allows the `bedrock:InvokeModel` action?")
        print("3. Bedrock Model Access: In the AWS Console, have you requested and been granted access to 'Claude 3 Sonnet' in the specified region?")
        print(f"4. AWS Region: Is the region in your `.env` file ('{aws_region}') the same one where you enabled the model in the console?")
        print("\n--- Detailed Error Traceback ---")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_connectivity_test()

