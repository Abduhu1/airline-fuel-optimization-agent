# streamlit_dashboard.py
#
# A platform-independent Streamlit web application that serves as a complete
# Mission Control Dashboard for the Airline Fuel Optimization Agent.
#
# Features:
# 1. Triggers new optimization jobs by sending messages to an AWS SQS input queue.
# 2. Polls an AWS SQS output queue to fetch and display completed optimization reports.
# 3. Loads all configuration (AWS region, queue URLs) from a .env file for security
#    and portability, making it fully platform-independent.
#
# How to Run:
# 1. Ensure your .env file is correctly configured with all necessary variables.
# 2. Make sure you have activated your Python virtual environment.
# 3. Run the command from your terminal: streamlit run streamlit_dashboard.py

import streamlit as st
import boto3
import json
import pandas as pd
import os
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, ClientError

# --- 1. CONFIGURATION & INITIALIZATION ---

# Load environment variables from the .env file.
# This is the core of making the app platform-independent.
load_dotenv()

# Fetch configuration from environment variables.
# The `os.getenv` method safely returns None if the variable is not found.
SQS_INPUT_QUEUE_URL = os.getenv("SQS_INPUT_QUEUE_URL")
SQS_OUTPUT_QUEUE_URL = os.getenv("SQS_OUTPUT_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1") # Default to us-east-1 if not set

# Set the page configuration for a better layout
st.set_page_config(layout="wide")

# --- 2. AWS AND DATA HANDLING FUNCTIONS ---

@st.cache_resource
def get_boto3_client(service_name):
    """
    Creates and caches a boto3 client to avoid re-creation on every rerun.
    Handles credential errors gracefully.
    """
    try:
        client = boto3.client(service_name, region_name=AWS_REGION)
        # A simple check to see if credentials are valid
        client.get_caller_identity()
        return client
    except NoCredentialsError:
        st.error("❌ AWS credentials not found. Please configure your credentials (e.g., in the .env file).")
        return None
    except ClientError as e:
        st.error(f"❌ AWS Client Error: {e}. Check your IAM permissions and AWS region.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during AWS client initialization: {e}")
        return None

@st.cache_data
def load_flight_plans():
    """
    Loads flight plan data from the local CSV file for the dropdown menu.
    Uses Streamlit's caching to avoid rereading the file on every interaction.
    """
    try:
        df = pd.read_csv("flight_plans.csv")
        return df['flight_id'].tolist()
    except FileNotFoundError:
        st.error("`flight_plans.csv` not found. Make sure it's in the same directory.")
        return []

def send_optimization_request(sqs_client, flight_id):
    """
    Sends a message to the SQS input queue to trigger a new optimization job.
    """
    if not sqs_client or not SQS_INPUT_QUEUE_URL:
        st.error("SQS client or input queue URL is not configured.")
        return False
    try:
        message_body = json.dumps({'flight_id': flight_id})
        sqs_client.send_message(
            QueueUrl=SQS_INPUT_QUEUE_URL,
            MessageBody=message_body
        )
        return True
    except ClientError as e:
        st.error(f"Failed to send message to SQS input queue: {e}")
        return False

def get_recommendations_from_sqs(sqs_client):
    """
    Polls the SQS output queue once and fetches all available result messages.
    """
    if not sqs_client or not SQS_OUTPUT_QUEUE_URL:
        # Don't show an error if output queue isn't configured, just return empty
        return []
    
    messages = []
    try:
        while True:
            response = sqs_client.receive_message(
                QueueUrl=SQS_OUTPUT_QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=1
            )
            if 'Messages' in response:
                for msg in response['Messages']:
                    messages.append(json.loads(msg['Body']))
                    # Clean up the message from the queue after processing
                    sqs_client.delete_message(QueueUrl=SQS_OUTPUT_QUEUE_URL, ReceiptHandle=msg['ReceiptHandle'])
            else:
                # No more messages in the queue
                break
    except ClientError as e:
        st.warning(f"Could not poll SQS output queue: {e}. Check URL and permissions.")
    return messages

# --- 3. STREAMLIT USER INTERFACE ---

st.title("✈️ Airline Fuel Optimization - Mission Control")

# Initialize boto3 client
sqs_client = get_boto3_client('sqs')

# Only proceed if the client was initialized successfully
if sqs_client:
    # --- Section for starting a new job ---
    st.header("Start a New Optimization Job")
    flight_ids = load_flight_plans()

    if flight_ids:
        selected_flight = st.selectbox("Select a Flight to Optimize:", flight_ids)
        if st.button("🚀 Launch Optimization Agent"):
            with st.spinner(f"Sending request for flight {selected_flight} to the agent..."):
                success = send_optimization_request(sqs_client, selected_flight)
                if success:
                    st.success(f"✅ Request for flight {selected_flight} sent successfully! The agent will now begin processing.")
                else:
                    st.error("Failed to send request. Please check the console for errors.")
    else:
        st.warning("Could not load flight IDs. Cannot start a new job.")

    st.markdown("---")

    # --- Section for displaying results ---
    st.header("Completed Optimization Reports")

    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []

    if st.button("🔄 Check for New Recommendations"):
        with st.spinner('Polling SQS for new optimization results...'):
            new_recs = get_recommendations_from_sqs(sqs_client)
            if new_recs:
                # Add new recommendations to the top of the list
                st.session_state.recommendations = new_recs + st.session_state.recommendations
                st.success(f"Found {len(new_recs)} new recommendation(s)!")
            else:
                st.info("No new recommendations found in the queue.")

    if not st.session_state.recommendations:
        st.info("No optimization recommendations loaded. Click the button above to check the queue.")
    else:
        # Display each recommendation in a formatted block
        for rec in st.session_state.recommendations:
            st.markdown("---")
            st.subheader(f"Report for Flight: `{rec.get('flight_id', 'N/A')}`")

            col1, col2, col3 = st.columns(3)
            col1.metric(label="Baseline Fuel Burn", value=f"{rec.get('baseline_fuel_kg', 0):,} kg")
            col2.metric(label="Optimized Fuel Burn", value=f"{rec.get('optimized_fuel_kg', 0):,} kg")
            savings = rec.get('fuel_saved_kg', 0)
            col3.metric(label="Projected Fuel Savings",
                        value=f"{savings:,} kg",
                        delta=f"-{savings:,} kg" if savings > 0 else None)

            with st.expander("View Agent's Rationale and Detailed Route"):
                st.text("Agent's Rationale:")
                st.info(rec.get('rationale', 'No rationale provided.'))

                st.text("Optimized Route:")
                # Ensure the route is a list before joining
                optimized_route = rec.get('optimized_route', [])
                if isinstance(optimized_route, list):
                    st.code(" -> ".join(map(str, optimized_route)))
                else:
                    st.code(str(optimized_route))
