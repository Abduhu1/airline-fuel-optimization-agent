# **Airline Fuel Optimization Agent**

## **1\. Overview**

The Airline Fuel Optimization Agent is a sophisticated proof-of-concept system that leverages an AI agent to analyze flight plans, real-time weather data, and aircraft performance models. Its mission is to recommend the most fuel-efficient flight routes and altitude profiles, directly addressing a critical operational cost for airlines.

This project demonstrates a modern, cloud-native, and decoupled architecture using **AWS Strands** for agentic orchestration, **Amazon Bedrock** for AI reasoning, and a robust **A\* search algorithm** for its core optimization logic. The entire workflow is designed to be event-driven and scalable, using **AWS SQS** as the primary message bus to separate the user-facing dashboard from the backend processing agent.

## **2\. System Architecture**

The system is designed as a decoupled, event-driven workflow, ensuring scalability and resilience. The user interface is separated from the core agentic processing via AWS SQS message queues, which act as the primary communication bus.

graph TD  
    subgraph User Interface & Interaction  
        A\[Operator\] \-- 1\. Initiates Optimization \--\> B{Streamlit Dashboard};  
        B \-- 2\. Publishes Flight ID to SQS\_Input\_Queue \--\> C((SQS Input Queue));  
    end

    subgraph "Agentic Core (AWS Lambda)"  
        D{Lambda Trigger} \-- 3\. Triggered by SQS Message \--\> E\[Fuel Agent\];  
        E \-- 4\. Executes System Prompt \--\> E;  
        E \-- 5\. Calls 'get\_flight\_plan' tool \--\> F\[flight\_plans.csv\];  
        F \-- 6\. Returns Flight Plan \--\> E;  
        E \-- 7\. Calls 'get\_weather\_for\_route' tool \--\> G\[Weather API\];  
        G \-- 8\. Returns Weather Data \--\> E;  
        E \-- 9\. Calls 'run\_fuel\_optimization' tool \--\> H\[A\* Optimization Engine w/ OpenAP\];  
        H \-- 10\. Returns Optimized Route \--\> E;  
        E \-- 11\. Calls 'publish\_recommendation' tool \--\> I{boto3 SQS Client};  
    end

    subgraph "Reporting Bus"  
        I \-- 12\. Sends Recommendation Message \--\> K((SQS Output Queue));  
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
| waypoints | String | A JSON-formatted list of ICAO codes representing the flight path. | \["JFK", "SWL", "PSB", "BZN", "SFO"\] |
| initial\_mass\_kg | Integer | The initial take-off mass of the aircraft in kilograms. | 150000 |
| aircraft\_type | String | The ICAO code for the specific aircraft model. | B772 |

## **6\. Setup and Installation Guide**

### **A. Local Environment (Conda)**

1. **Clone the Repository:**  
   git clone \[https://github.com/YOUR\_USERNAME/airline-fuel-optimizer.git\](https://github.com/YOUR\_USERNAME/airline-fuel-optimizer.git)  
   cd airline-fuel-optimizer

2. **Create and Activate Conda Environment:**  
   conda create \-n fuel\_agent python=3.11 \-y  
   conda activate fuel\_agent

3. **Install Dependencies:**  
   pip install \-r requirements.txt

4. Configure AWS Credentials:  
   On macOS/Linux:  
   export AWS\_ACCESS\_KEY\_ID="YOUR\_KEY\_HERE"  
   export AWS\_SECRET\_ACCESS\_KEY="YOUR\_SECRET\_HERE"  
   export AWS\_REGION="us-east-1"

   *On Windows (Command Prompt):*  
   set AWS\_ACCESS\_KEY\_ID="YOUR\_KEY\_HERE"  
   set AWS\_SECRET\_ACCESS\_KEY="YOUR\_SECRET\_HERE"  
   set AWS\_REGION="us-east-1"

### **B. Local Environment (venv)**

1. Create and Activate Virtual Environment:  
   On macOS/Linux:  
   python3 \-m venv venv  
   source venv/bin/activate

   *On Windows:*  
   python \-m venv venv  
   .\\venv\\Scripts\\activate

2. **Install Dependencies & Configure Credentials:** Follow steps 3 and 4 from the Conda setup.

### **C. Cloud Environment (Google Colab)**

1. **Configure AWS Credentials Securely:** Use the **Secrets Manager** (key icon) to add AWS\_ACCESS\_KEY\_ID and AWS\_SECRET\_ACCESS\_KEY.  
2. **Setup Cell:** Run this in the first cell of your notebook.  
   \# Install all required packages  
   \!pip install \-r requirements.txt

   \# Load secrets securely into the environment  
   import os  
   from google.colab import userdata

   os.environ\['AWS\_ACCESS\_KEY\_ID'\] \= userdata.get('AWS\_ACCESS\_KEY\_ID')  
   os.environ\['AWS\_SECRET\_ACCESS\_KEY'\] \= userdata.get('AWS\_SECRET\_ACCESS\_KEY')  
   os.environ\['AWS\_REGION'\] \= "us-east-1" \# Or your preferred region

## **7\. How to Run the Application**

### **Step 1: Start the User Interface**

Open a terminal (with your environment activated) and run:

streamlit run streamlit1.py

### **Step 2: Run the Agent Logic**

Open a **separate terminal** (with your environment activated) and run:

python notebook\_style\_runner.py

### **Step 3: View Results**

Go back to your Streamlit dashboard and click the **"Check for New Recommendations"** button.

## **8\. Deployment to AWS Lambda**

### **Build and Deploy Steps**

1. **Build the Docker Image:**  
   docker build \--no-cache \-t fuel-optimization-agent \-f Dockerfile2 .

2. **Push to Amazon ECR** and create a Lambda function using the container image URI.

## **9\. License**

This project is licensed under the MIT License. See the LICENSE file for details.