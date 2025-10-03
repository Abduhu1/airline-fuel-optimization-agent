Airline Fuel Optimization AgentAn AI agent, built with the AWS Strands SDK, that analyzes flight plans and weather data to recommend the most fuel-efficient route and altitude profile. This agent is designed for and has been tested with serverless deployment on AWS Lambda.OverviewThis project implements an autonomous AI agent designed to tackle the complex challenge of airline fuel optimization. The agent orchestrates a series of tools to fetch flight data, retrieve weather forecasts, and execute a sophisticated A* search algorithm to discover the path with the lowest possible fuel consumption.The system is architected with a serverless-first philosophy. While it can be run locally for testing, the primary deployment target is AWS Lambda, allowing for a scalable, event-driven, and cost-efficient solution. The agent communicates its findings asynchronously via an AWS SQS queue, making it a robust and decoupled component for integration into modern aviation operations systems.ArchitectureThe system uses a message-driven, serverless architecture. The primary execution environment is AWS Lambda, but the project also supports local development and visualization with Streamlit.graph TD;
    %% Define fontawesome icons for better visualization
    subgraph "Local Development & Testing Environment"
        direction LR
        dev[Developer] --> |1. Runs command| cli[ `python notebook_style_runner.py LH505`]
        cli --> |2. Loads config| env[ .env file]
        cli --> |3. Executes Agent Logic| local_agent[Strands Agent (Local)]

        subgraph "Local Result Visualization"
            streamlit_app[Streamlit Dashboard] --> |9. Polls for results| sqs_output
            dev --> |Runs `streamlit run`| streamlit_app
        end
    end

    subgraph "AWS Cloud Production Environment"
        direction TB
        subgraph "Deployment Pipeline"
            direction LR
            repo[Code Repository] -->|'docker build'| docker[Docker Image]
            docker -->|'docker push'| ecr[Amazon ECR]
        end

        subgraph "Serverless Execution"
            direction TB
            sqs_input[SQS Input Queue] -- "4a. Event: `{'flight_id': '...'}`" --> lambda_func(AWS Lambda Function)
            ecr --> |Deploys Image| lambda_func
            lambda_func -- "Contains" --> lambda_agent[Strands Agent (Lambda)]
        end
    end

    subgraph "Shared AWS & External Services"
        direction TB
        bedrock[Amazon Bedrock]
        weather[Weather API]
        sqs_output[SQS Output Queue]
    end

    %% --- Data and Logic Flows ---
    local_agent --> |4. Fetches flight data| data_csv[flight_plans.csv]
    lambda_agent --> |4b. Fetches flight data| data_csv_lambda[flight_plans.csv (in container)]
    local_agent --> |5. Invokes LLM| bedrock
    lambda_agent --> |5b. Invokes LLM| bedrock
    local_agent --> |6. Fetches weather| weather
    lambda_agent --> |6b. Fetches weather| weather
    local_agent --> |8. Publishes Recommendation| sqs_output
    lambda_agent --> |8b. Publishes Recommendation| sqs_output

    classDef aws fill:#232F3E,stroke:#FF9900,stroke-width:2px,color:#fff;
    class ecr,lambda_func,sqs_input,sqs_output,bedrock aws;
Technology StackAI/ML: AWS Strands SDK, Amazon Bedrock (Claude 3 Sonnet)Cloud Provider & Serverless: AWS Lambda, AWS SQS, Amazon BedrockContainerization: Docker (for Lambda deployment)Backend: Python 3.11+Core Libraries: Pandas, OpenAP, Boto3, Requests, python-dotenvLocal UI Demo: StreamlitAWS Prerequisites & IAM PoliciesBefore running this project, you must configure the necessary AWS resources and permissions. See the guide in this document for creating an IAM User, enabling Bedrock Model Access, and the minimal IAM policies for Bedrock, SQS, and ECR.Code StructureThis project provides two primary, self-contained Python scripts: one for cloud deployment and one for local development.lambda_handler.py: The all-in-one script for AWS Lambda. It contains the complete agent logic and the handler function required by AWS. This is the only application script needed for the production deployment.notebook_style_runner.py: A self-contained script for easy, interactive testing in a local IDE (like VS Code or PyCharm). It includes all code in a single file, similar to a Jupyter/Colab notebook, making it a great starting point for experimentation.requirements.txt: Dependencies for local development.requirements-lambda.txt: Minimal dependencies for the production AWS Lambda deployment.Deployment (Production on AWS Lambda)The primary method for deploying the agent is via AWS Lambda using a container image.Essential Files for DeploymentThe Docker build process bundles the following files into the container image:Dockerfilerequirements-lambda.txtlambda_handler.py (contains all agent logic)flight_plans.csvDeployment StepsBuild the Docker Image:docker build --no-cache -t fuel-optimization-agent .
Push to Amazon ECR and create the Lambda function from the container image, assigning the correct IAM execution role and environment variables.Local Setup and Testing GuideStep 1: Clone & ConfigureClone the repository.Rename .env.example to .env and fill in your IAM User credentials and SQS queue URLs.Step 2: Install Dependencies# Create and activate a virtual environment
python -m venv venv
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate

# Install all required Python packages for local development
pip install -r requirements.txt
Step 3: Run the Agent LocallyUse the notebook-style runner for all local testing. This all-in-one script is great for quick, self-contained testing and experimentation.python notebook_style_runner.py UA123
LicenseThis project is licensed under the MIT License - see the LICENSE file for details.