# **Airline Fuel Optimization Agent**

([https://img.shields.io/badge/AWS-Bedrock%2C%20Lambda%2C%20SQS-orange.svg](https://www.google.com/search?q=https://img.shields.io/badge/AWS-Bedrock%252C%2520Lambda%252C%2520SQS-orange.svg))\]([https://aws.amazon.com/](https://aws.amazon.com/)) ([https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b](https://www.google.com/search?q=https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b))\]([https://streamlit.io](https://streamlit.io))

## **1\. Overview**

The Airline Fuel Optimization Agent is a sophisticated proof-of-concept system that leverages an AI agent to analyze flight plans, real-time weather data, and aircraft performance models. Its mission is to recommend the most fuel-efficient flight routes and altitude profiles, directly addressing a critical operational cost for airlines.

This project demonstrates a modern, cloud-native, and decoupled architecture using **AWS Strands** for agentic orchestration, **Amazon Bedrock** for AI reasoning, and a robust **A\* search algorithm** for its core optimization logic. The entire workflow is designed to be event-driven and scalable, using **AWS SQS** as the primary message bus to separate the user-facing dashboard from the backend processing agent.

## **2\. System Architecture**

The system is designed as a decoupled, event-driven workflow, ensuring scalability and resilience. The user interface is separated from the core agentic processing via AWS SQS message queues, which act as the primary communication bus.

Code snippet

graph TD  
    subgraph User Interface & Interaction  
        A\[Operator\] \-- 1\. Initiates Optimization \--\> B{Streamlit Dashboard};  
        B \-- 2\. Publishes Flight ID to SQS\_Input\_Queue \--\> C;  
    end

    subgraph Agentic Core on AWS Lambda  
        D{Lambda Trigger} \-- 3\. Triggered by SQS Message \--\> E;  
        E \-- 4\. Executes System Prompt \--\> E;  
        E \-- 5\. Calls 'get\_flight\_plan' tool \--\> F\[flight\_plans.csv\];  
        F \-- 6\. Returns Flight Plan \--\> E;  
        E \-- 7\. Calls 'get\_weather\_for\_route' tool \--\> G;  
        G \-- 8\. Returns Weather Data \--\> E;  
        E \-- 9\. Calls 'run\_fuel\_optimization' tool \--\> H\[A\* Optimization Engine w/ OpenAP\];  
        H \-- 10\. Returns Optimized Route \--\> E;  
        E \-- 11\. Calls 'publish\_recommendation' tool \--\> I{boto3 SQS Client};  
    end

    subgraph Reporting Bus  
        I \-- 12\. Sends Recommendation Message \--\> K;  
    end

    subgraph Reporting & Monitoring  
        B \-- 13\. Polls SQS\_Output\_Queue for Results \--\> K;  
        K \-- 14\. Delivers Recommendation Message \--\> B;  
        B \-- 15\. Displays Results \--\> A;  
    end

    style C fill:\#FF9900,stroke:\#333,stroke-width:2px  
    style K fill:\#FF9900,stroke:\#333,stroke-width:2px  
    style E fill:\#232F3E,stroke:\#FF9900,stroke-width:2px,color:\#fff  
    style B fill:\#FF4B4B,stroke:\#333,stroke-width:2px,color:\#fff

## **3\. Features**

* **Agent-Driven Workflow:** Utilizes the **AWS Strands SDK** for a model-driven agent that orchestrates the entire optimization process.  
* **A\* Based Optimization:** Implements a scientifically sound A\* search algorithm to find the optimal path across a 3D graph of waypoints and flight levels.  
* **Physics-Based Fuel Modeling:** Integrates the openap library to provide credible fuel burn estimates.  
* **Real-time Weather Integration:** Fetches current METAR and TAF weather reports to inform the optimization model.  
* **Decoupled & Scalable Architecture:** Uses **AWS SQS** as a robust, cloud-native message bus to create a resilient, event-driven system.  
* **Interactive Dashboard:** A **Streamlit**\-based "Mission Control Dashboard" provides a user-friendly interface for initiating optimizations and viewing results.  
* **Cloud-Native Deployment:** Containerized with **Docker** for reproducible and scalable deployment on serverless platforms like **AWS Lambda**.

## **4\. Technology Stack**

| Technology | Role |
| :---- | :---- |
| 🐍 **Python 3.11+** | Core programming language for all components. |
| 🧠 **AWS Strands** | Open-source SDK for building the AI agent. |
| 🤖 **Amazon Bedrock** | Provides the Claude 3 Sonnet LLM for agent reasoning. |
| 📨 **AWS SQS** | Cloud-native message queue for decoupling services. |
| 📦 **Docker** | Containerization for reproducible deployment. |
| ☁️ **AWS Lambda** | Serverless compute for the backend agent. |
| 📊 **Streamlit** | Framework for the interactive web dashboard. |
| ✈️ **OpenAP** | Library for aircraft performance modeling. |

## **5\. Dataset Used**

The proof-of-concept relies on a sample dataset named flight\_plans.csv. This file contains mock flight plans that serve as the input for the optimization agent.

**File Structure:**

| Column | Data Type | Description | Example |
| :---- | :---- | :---- | :---- |
| flight\_id | String | A unique identifier for the flight. | UA123 |
| origin\_airport | String | The ICAO code for the flight's origin airport. | KJFK |
| destination\_airport | String | The ICAO code for the flight's destination airport. | KSFO |
| waypoints | String | A JSON-formatted list of ICAO codes representing the flight path. | "" |
| initial\_mass\_kg | Integer | The initial take-off mass of the aircraft in kilograms. | 150000 |
| aircraft\_type | String | The ICAO code for the specific aircraft model. | B772 |

## **6\. Setup and Installation Guide**

This project is designed to be platform-independent. This guide provides distinct instructions for local development (using Conda or venv) and cloud-based development with Google Colab.

### **A. Local Environment (Conda)**

*Recommended for a clean, isolated environment on Windows, macOS, or Linux.*

1. **Prerequisites:**  
   * Git  
   * Anaconda or Miniconda  
2. **Clone the Repository:**  
   Bash  
   git clone https://github.com/YOUR\_USERNAME/airline-fuel-optimizer.git  
   cd airline-fuel-optimizer

3. **Create and Activate Conda Environment:**  
   Bash  
   conda create \-n fuel\_agent python=3.11 \-y  
   conda activate fuel\_agent

4. **Install Dependencies:** This project uses requirements.txt for local development.  
   Bash  
   pip install \-r requirements.txt

5. Configure AWS Credentials:  
   IMPORTANT: Never hardcode your credentials. Set them as environment variables.  
   * **On macOS/Linux:**  
     Bash  
     export AWS\_ACCESS\_KEY\_ID="YOUR\_KEY\_HERE"  
     export AWS\_SECRET\_ACCESS\_KEY="YOUR\_SECRET\_HERE"  
     export AWS\_REGION="us-east-1" \# Or your preferred region

   * **On Windows (Command Prompt):**  
     DOS  
     set AWS\_ACCESS\_KEY\_ID="YOUR\_KEY\_HERE"  
     set AWS\_SECRET\_ACCESS\_KEY="YOUR\_SECRET\_HERE"  
     set AWS\_REGION="us-east-1"

### **B. Local Environment (venv)**

*An alternative to Conda using Python's built-in virtual environment manager.*

1. **Prerequisites & Cloning:** Follow steps 1 and 2 from the Conda setup.  
2. **Create and Activate Virtual Environment:**  
   * **On macOS/Linux:**  
     Bash  
     python3 \-m venv venv  
     source venv/bin/activate

   * **On Windows:**  
     DOS  
     python \-m venv venv

.\\venv\\Scripts\\activate\`\`\`

3. **Install Dependencies & Configure Credentials:** Follow steps 4 and 5 from the Conda setup.

### **C. Cloud Environment (Google Colab)**

*Ideal for a standardized, cloud-based development environment that ensures perfect reproducibility.*

1. **Upload Project Files:**  
   * In a new Google Colab notebook, use the file browser on the left to upload all your project files (.py files, .csv, requirements.txt, etc.).  
2. **Configure AWS Credentials (Securely):**  
   * In the Colab interface, click the **"Key"** icon in the left sidebar to open the **Secrets Manager**.  
   * Create two new secrets: AWS\_ACCESS\_KEY\_ID and AWS\_SECRET\_ACCESS\_KEY.  
   * Paste your corresponding AWS credentials into the value fields. This is the most secure way to handle secrets in Colab.  
3. Setup Cell:  
   In the first cell of your notebook, run the following commands to install dependencies and load your secrets into the environment.  
   Python  
   \# Install all required packages from your requirements file

\!pip install \-r requirements.txt

\# Load secrets securely into the environment  
import os  
from google.colab import userdata

os.environ \= userdata.get('AWS\_ACCESS\_KEY\_ID')  
os.environ \= userdata.get('AWS\_SECRET\_ACCESS\_KEY')  
os.environ \= "us-east-1" \# Or your preferred region  
\`\`\`

## **7\. How to Run the Application**

Follow these steps to run the full application workflow in your local or Colab environment.

### **Step 0: (Optional) Test Connectivity**

Before running the full application, you can use initial\_connectivity\_test.py to verify that your environment is correctly configured to communicate with AWS Bedrock.

Bash

python initial\_connectivity\_test.py

A successful run will print a response from the AI model, confirming your credentials and permissions are working.

### **Step 1: Start the User Interface**

The **Streamlit Dashboard** is the primary user interface for this application. It allows you to initiate optimization tasks and view the results.

Open a terminal (with your virtual environment activated) and run:

Bash

streamlit run streamlit1.py

This will open the dashboard in your web browser. Interacting with the dashboard will send a message to your input SQS queue, ready to be processed by the agent.

### **Step 2: Run the Agent Logic**

The main agent logic in evaluation\_codefile.py is designed to be triggered by an event in the cloud. For local testing, you can run this file directly. It will perform the optimization and publish the result to your output SQS queue.

Open a **separate terminal** (with your environment activated) and run:

Bash

python evaluation\_codefile.py

**Note:** For this to work, evaluation\_codefile.py should contain a main execution block (e.g., if \_\_name\_\_ \== "\_\_main\_\_"). This is a standard Python practice that makes a module runnable as a script for testing purposes.

### **Step 3: View Results**

Go back to your Streamlit dashboard in the browser and click the **"Check for New Recommendations"** button. The dashboard will poll the output SQS queue and display the optimization results sent by the agent.

## **8\. Deployment to AWS Lambda**

The core agent is designed for serverless deployment on **AWS Lambda** using a container image. This section outlines the process.

### **Dependency Management**

This project uses two separate requirements files:

* requirements.txt: For local development and IDE support.  
* requirements-lambda.txt: A minimal set of dependencies for the production Lambda environment.

### **Dockerfile Configuration**

The provided Dockerfile2 is configured to build the Lambda deployment package. It expects the Lambda handler code to be in a file named lambda\_handler.py and the dependencies to be listed in requirements-lambda.txt.

### **Build and Deploy Steps**

1. Build the Docker Image:  
   This command builds the container image. The \--no-cache flag is recommended to ensure a fresh build with the latest versions of your files and base images.  
   Bash  
   docker build \--no-cache \-t fuel-optimization-agent \-f Dockerfile2.

2. Push to Amazon ECR:  
   Push the built image to an Amazon Elastic Container Registry (ECR) repository in your AWS account.  
3. Create Lambda Function:  
   Create a new AWS Lambda function. In the configuration, select "Container image" and provide the Image URI from your ECR repository. Set up an SQS trigger to invoke the function automatically when new flight optimization requests arrive in your input queue.

## **9\. License**

This project is licensed under the MIT License. See the LICENSE file for details.