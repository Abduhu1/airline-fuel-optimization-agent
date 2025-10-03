```mermaid
graph TD
    %% Safe Mermaid for GitHub: no HTML tags, no backticks in labels, no line-wrapped node titles

    subgraph Local_Dev["Local Development & Testing Environment"]
        direction LR
        dev[Developer] -->|1. Runs command| cli[python fuel_optimization_agent.py LH505]
        cli -->|2. Loads config| env[.env file (AWS Credentials)]
        cli -->|3. Executes Agent Logic| local_agent[Strands Agent (Running Locally)]

        subgraph Local_Viz["Local Result Visualization"]
            streamlit_app[Streamlit Dashboard] -->|9. Polls for results| sqs_output
            dev -->|Runs streamlit run| streamlit_app
        end
    end

    subgraph AWS_Cloud["AWS Cloud Production Environment"]
        direction TB
        subgraph Deploy_Pipeline["Deployment Pipeline"]
            direction LR
            repo[Code Repository (Dockerfile, lambda_handler.py)] -->|docker build| docker_img[Docker Image]
            docker_img -->|docker push| ecr[Amazon ECR (Container Registry)]
        end

        subgraph Serverless_Exec["Serverless Execution"]
            direction TB
            sqs_input[SQS Input Queue (Trigger)] -->|4a. Event: {'flight_id': '...'}| lambda_func[AWS Lambda Function]
            ecr -->|Deploys Image| lambda_func
            lambda_func -->|Contains| lambda_agent[Strands Agent (Running in Lambda)]
        end
    end

    subgraph Shared_Services["Shared AWS & External Services"]
        direction TB
        bedrock[Amazon Bedrock (Claude 3 Sonnet)]
        weather[Weather API (open-meteo.com)]
        sqs_output[SQS Output Queue (Results Bus)]
    end

    %% --- Data and Logic Flows ---
    local_agent -->|4. Fetches flight data| data_csv[flight_plans.csv]
    lambda_agent -->|4b. Fetches flight data| data_csv_lambda[flight_plans.csv (packaged in container)]

    local_agent -->|5. Invokes LLM| bedrock
    lambda_agent -->|5b. Invokes LLM| bedrock

    local_agent -->|6. Fetches weather| weather
    lambda_agent -->|6b. Fetches weather| weather

    local_agent -->|7. Runs A* Search and OpenAP| local_agent
    lambda_agent -->|7b. Runs A* Search and OpenAP| lambda_agent

    local_agent -->|8. Publishes Recommendation| sqs_output
    lambda_agent -->|8b. Publishes Recommendation| sqs_output

    %% Styling
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px,color:#333
    classDef aws fill:#232F3E,stroke:#FF9900,stroke-width:2px,color:#fff
    class ecr,lambda_func,sqs_input,sqs_output,bedrock aws
    classDef local fill:#ECEFF1,stroke:#37474F,stroke-width:2px
    class dev,cli,env,local_agent,streamlit_app,repo local
    classDef external fill:#E3F2FD,stroke:#1565C0,stroke-width:2px
    class weather external
    classDef data fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    class data_csv,data_csv_lambda data
    classDef docker_style fill:#3399ff,stroke:#fff,stroke-width:2px,color:white
    class docker_img docker_style
```

