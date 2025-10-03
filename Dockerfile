# --- STAGE 1: Build dependencies in a full Python environment ---
FROM python:3.11-slim as builder

# Install system dependencies that might be needed by Python packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential

# Set the working directory
WORKDIR /install_root

# Copy only the Lambda requirements file to leverage Docker cache
COPY requirements-lambda.txt .

# Install the Python dependencies into a target directory
RUN pip install --no-cache-dir --target="./packages" -r requirements-lambda.txt

# --- STAGE 2: Create the final, lean Lambda image ---
FROM public.ecr.aws/lambda/python:3.11

# Set the working directory in the Lambda environment
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the pre-installed packages from the builder stage
COPY --from=builder /install_root/packages ./

# Copy the application code and data required for execution
COPY fuel_optimization_agent.py .
COPY lambda_handler.py .
COPY flight_plans.csv .

# Set the command to run when the container starts.
# AWS Lambda will invoke the 'handler' function within the 'lambda_handler' file.
CMD [ "lambda_handler.handler" ]

