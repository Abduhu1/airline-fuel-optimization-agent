graph TD;
    %% Define fontawesome icons for better visualization
    %% classDef aws fill:#FF9900,stroke:#333,stroke-width:2px;

    subgraph "Local Development & Testing Environment"
        direction LR
        dev[<i class='fa fa-user'></i> Developer] --> |1. Runs command| cli[<i class='fa fa-terminal'></i> `python fuel_optimization_agent.py LH505`]
        cli --> |2. Loads config| env[<i class='fa fa-file-code'></i> .env file<br>(AWS Credentials)]
        cli --> |3. Executes Agent Logic| local_agent[<i class='fa fa-cogs'></i> Strands Agent<br>(Running Locally)]

        subgraph "Local Result Visualization"
            streamlit_app[<i class='fa fa-desktop'></i> Streamlit Dashboard] --> |9. Polls for results| sqs_output
            dev --> |Runs `streamlit run`| streamlit_app
        end
    end

    subgraph "AWS Cloud Production Environment"
        direction TB
        subgraph "Deployment Pipeline"
            direction LR
            repo[<i class='fa fa-git-square'></i> Code Repository<br>(Dockerfile, lambda_handler.py)] -->|'docker build'| docker[<i class='fab fa-docker'></i> Docker Image]
            docker -->|'docker push'| ecr[<i class='fa fa-aws'></i> Amazon ECR<br>(Container Registry)]
        end

        subgraph "Serverless Execution"
            direction TB
            sqs_input[<i class='fa fa-aws'></i> SQS Input Queue<br>(Trigger)] -- "4a. Event: `{'flight_id': '...'}`" --> lambda_func
            ecr --> |Deploys Image| lambda_func(<i class='fa fa-aws'></i> AWS Lambda Function)
            lambda_func -- "Contains" --> lambda_agent[<i class='fa fa-cogs'></i> Strands Agent<br>(Running in Lambda)]
        end
    end

    subgraph "Shared AWS & External Services"
        direction TB
        bedrock[<i class='fa fa-aws'></i> Amazon Bedrock<br>(Claude 3 Sonnet)]
        weather[<i class='fa fa-cloud'></i> Weather API<br>(open-meteo.com)]
        sqs_output[<i class='fa fa-aws'></i> SQS Output Queue<br>(Results Bus)]
    end

    %% --- Data and Logic Flows ---

    %% Agent Interactions (Local and Lambda)
    local_agent --> |4. Fetches flight data| data_csv[<i class='fa fa-file-csv'></i> flight_plans.csv]
    lambda_agent --> |4b. Fetches flight data| data_csv_lambda[<i class='fa fa-file-csv'></i> flight_plans.csv<br>(packaged in container)]

    local_agent --> |5. Invokes LLM| bedrock
    lambda_agent --> |5b. Invokes LLM| bedrock

    local_agent --> |6. Fetches weather| weather
    lambda_agent --> |6b. Fetches weather| weather

    local_agent --> |7. Runs A* Search & OpenAP| local_agent
    lambda_agent --> |7b. Runs A* Search & OpenAP| lambda_agent

    local_agent --> |8. Publishes Recommendation| sqs_output
    lambda_agent --> |8b. Publishes Recommendation| sqs_output


    %% Styling and links to make it look professional
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px,color:#333;
    classDef aws fill:#232F3E,stroke:#FF9900,stroke-width:2px,color:#fff;
    class ecr,lambda_func,sqs_input,sqs_output,bedrock aws;
    classDef local fill:#ECEFF1,stroke:#37474F,stroke-width:2px;
    class dev,cli,env,local_agent,streamlit_app,repo local;
    classDef external fill:#E3F2FD,stroke:#1565C0,stroke-width:2px;
    class weather external;
    classDef data fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px;
    class data_csv,data_csv_lambda data;
    classDef docker_style fill:#3399ff,stroke:#fff,stroke-width:2px,color:white;
    class docker docker_style

