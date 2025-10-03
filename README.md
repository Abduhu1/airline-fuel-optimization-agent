# **Airline Fuel Optimization Agent**

An AI agent, built with the AWS Strands SDK, that analyzes flight plans and weather data to recommend the most fuel-efficient route and altitude profile. This agent is designed for and has been tested with serverless deployment on **AWS Lambda**.

## **Overview**

This project implements an autonomous AI agent designed to tackle the complex challenge of airline fuel optimization. The agent orchestrates a series of tools to fetch flight data, retrieve weather forecasts, and execute a sophisticated A\* search algorithm to discover the path with the lowest possible fuel consumption.

The system is architected with a **serverless-first** philosophy. While it can be run locally for testing, the primary deployment target is AWS Lambda, allowing for a scalable, event-driven, and cost-efficient solution. The agent communicates its findings asynchronously via an AWS SQS queue, making it a robust and decoupled component for integration into modern aviation operations systems.

## **Architecture**

The system uses a message-driven, serverless architecture. The primary execution environment is AWS Lambda, but the project also supports local development and visualization with an interactive Streamlit dashboard.

graph TD;  
    %% Define fontawesome icons for better visualization  
    subgraph "Local Development & Testing Environment"  
        direction LR  
        dev\[Developer\] \--\> |1. Runs command| cli\[ \`python notebook\_style\_runner.py LH505\`\]  
        cli \--\> |2. Loads config| env\[ .env file\]  
        cli \--\> |3. Executes Agent Logic| local\_agent\[Strands Agent (Local)\]

        subgraph "Local Result Visualization"  
            streamlit\_app\[Streamlit Dashboard\] \--\> |9. Polls for results| sqs\_output  
            streamlit\_app \--\> |Sends Trigger| sqs\_input  
            dev \--\> |Runs \`streamlit run\`| streamlit\_app  
        end  
    end

    subgraph "AWS Cloud Production Environment"  
        direction TB  
        subgraph "Deployment Pipeline"  
            direction LR  
            repo\[Code Repository\] \--\>|'docker build'| docker\[Docker Image\]  
            docker \--\>|'docker push'| ecr\[Amazon ECR\]  
        end

        subgraph "Serverless Execution"  
            direction TB  
            sqs\_input\[SQS Input Queue\] \-- "4a. Event: \`{'flight\_id': '...'}\`" \--\> lambda\_func(AWS Lambda Function)  
            ecr \--\> |Deploys Image| lambda\_func  
            lambda\_func \-- "Contains" \--\> lambda\_agent\[Strands Agent (Lambda)\]  
        end  
    end

    subgraph "Shared AWS & External Services"  
        direction TB  
        bedrock\[Amazon Bedrock\]  
        weather\[Weather API\]  
        sqs\_output\[SQS Output Queue\]  
    end

    %% \--- Data and Logic Flows \---  
    local\_agent \--\> |4. Fetches flight data| data\_csv\[flight\_plans.csv\]  
    lambda\_agent \--\> |4b. Fetches flight data| data\_csv\_lambda\[flight\_plans.csv (in container)\]  
    local\_agent \--\> |5. Invokes LLM| bedrock  
    lambda\_agent \--\> |5b. Invokes LLM| bedrock  
    local\_agent \--\> |6. Fetches weather| weather  
    lambda\_agent \--\> |6b. Fetches weather| weather  
    local\_agent \--\> |8. Publishes Recommendation| sqs\_output  
    lambda\_agent \--\> |8b. Publishes Recommendation| sqs\_output

    classDef aws fill:\#232F3E,stroke:\#FF9900,stroke-width:2px,color:\#fff;  
    class ecr,lambda\_func,sqs\_input,sqs\_output,bedrock aws;

## **Technology Stack**

* **AI/ML**: AWS Strands SDK, Amazon Bedrock (Claude 3 Sonnet)  
* **Cloud Provider & Serverless**: **AWS Lambda**, AWS SQS, Amazon Bedrock  
* **Containerization**: **Docker** (for Lambda deployment)  
* **Backend**: Python 3.11+  
* **Core Libraries**: Pandas, OpenAP, Boto3, Requests, python-dotenv  
* **Local UI**: Streamlit Mission Control Dashboard

## **AWS Prerequisites & IAM Policies**

Before running this project, you must configure the necessary AWS resources and permissions. See the guide in this document for creating an IAM User, enabling Bedrock Model Access, and the minimal IAM policies for Bedrock, SQS, and ECR.

## **Code Structure**

This project provides separate, self-contained Python scripts for cloud deployment and local development.

* **lambda\_handler.py**: The **all-in-one script for AWS Lambda**. It contains the complete agent logic and the handler function required by AWS. This is the only application script needed for the production deployment.  
* **notebook\_style\_runner.py**: A **self-contained script for easy, interactive testing in a local IDE** (like VS Code or PyCharm). It is a great starting point for experimentation.  
* **streamlit\_dashboard.py**: A **fully-featured, platform-independent web dashboard** for local use. It can trigger new agent runs and display the results, serving as a complete mission control UI.  
* **requirements.txt**: Dependencies for **local development**.  
* **requirements-lambda.txt**: Minimal dependencies for the **production AWS Lambda deployment**.

## **Deployment (Production on AWS Lambda)**

The primary method for deploying the agent is via AWS Lambda using a container image.

### **Essential Files for Deployment**

The Docker build process bundles the following files into the container image:

* Dockerfile  
* requirements-lambda.txt  
* lambda\_handler.py (contains all agent logic)  
* flight\_plans.csv

### **Deployment Steps**

1. **Build the Docker Image**:  
   docker build \--no-cache \-t fuel-optimization-agent .

2. **Push to Amazon ECR** and create the Lambda function from the container image, assigning the correct IAM execution role and environment variables.

## **Local Setup and Testing Guide**

### **Step 1: Clone & Configure**

1. Clone the repository.  
2. Rename .env.example to .env and fill in your AWS credentials and **both SQS queue URLs**.

### **Step 2: Install Dependencies**

\# Create and activate a virtual environment  
python \-m venv venv  
\# On Windows: venv\\Scripts\\activate  
\# On macOS/Linux: source venv/bin/activate

\# Install all required Python packages for local development  
pip install \-r requirements.txt

### **Step 3: Run the Application Locally**

You have two main ways to interact with the project on your local machine.

#### **Option A: Run the Notebook-Style Runner (for direct testing)**

This script is great for quick, self-contained testing and experimentation directly in your terminal.

python notebook\_style\_runner.py UA123

#### **Option B: Launch the Mission Control Dashboard (Recommended UI)**

This provides a full web interface to trigger agent runs and view results.

streamlit run streamlit\_dashboard.py

## **License**

This project is licensed under the MIT License \- see the [LICENSE](https://www.google.com/search?q=./LICENSE) file for details.