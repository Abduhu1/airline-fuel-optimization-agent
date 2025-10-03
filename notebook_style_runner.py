# === Fuel Optimization Agent: Standalone Optimizer ===
#
# Author: [Your Name/Team Name]
# Date: [Current Date]
#
# This single file contains the entire application, refactored from its original
# Colab notebook format to be runnable in any local Integrated Development Environment (IDE)
# such as Visual Studio Code, PyCharm, etc. It is designed for easy, self-contained
# testing and experimentation.

# --- How to Run This Script ---
# 1. Ensure you have a .env file in the same directory. You can create one by
#    renaming the `.env.example` file and filling in your AWS credentials.
# 2. Open a terminal or the integrated terminal in your IDE.
# 3. Run the script from the command line, providing a flight ID as an argument.
#    For example:
#    python standalone_optimizer.py LH505

# Section 1: All Necessary Imports
import os
import json
import heapq
import math
import boto3
import requests
import argparse  # Standard library for parsing command-line arguments
from dotenv import load_dotenv  # Used to load credentials from the .env file
from strands import Agent, tool
from openap import FuelFlow # Core library for fuel burn calculations

# Load environment variables from a .env file at the very start of the script.
# This makes environment variables available to the rest of the application.
load_dotenv()

# Section 2: Hardcoded Data Sources (Flight Plans, Coordinates, and City Names)
# NOTE: For this self-contained script, flight data is kept internally for simplicity.
# In the modular, production-ready version of the project (`fuel_optimization_agent.py`),
# this data is loaded dynamically from the `flight_plans.csv` file.
ALL_FLIGHT_PLANS = [
    {'flight_id': 'UA123', 'origin_airport': 'KJFK', 'destination_airport': 'KSFO', 'waypoints': ['KJFK', 'KORD', 'KSFO'], 'initial_mass_kg': 150000, 'aircraft_type': 'B772'},
    {'flight_id': 'AA456', 'origin_airport': 'KLAX', 'destination_airport': 'EGLL', 'waypoints': ['KLAX', 'CYUL', 'EIDW', 'EGLL'], 'initial_mass_kg': 180000, 'aircraft_type': 'B789'},
    {'flight_id': 'DL789', 'origin_airport': 'KATL', 'destination_airport': 'RJTT', 'waypoints': ['KATL', 'KSEA', 'PANC', 'RJTT'], 'initial_mass_kg': 200000, 'aircraft_type': 'A35K'},
    {'flight_id': 'SW101', 'origin_airport': 'EDDF', 'destination_airport': 'ZSPD', 'waypoints': ['EDDF', 'UUEE', 'UNNT', 'ZSPD'], 'initial_mass_kg': 195000, 'aircraft_type': 'B744'},
    {'flight_id': 'QF202', 'origin_airport': 'YSSY', 'destination_airport': 'KDFW', 'waypoints': ['YSSY', 'NFFN', 'KLAX', 'KDFW'], 'initial_mass_kg': 175000, 'aircraft_type': 'A388'},
    {'flight_id': 'EK303', 'origin_airport': 'OMDB', 'destination_airport': 'SBGR', 'waypoints': ['OMDB', 'HBEG', 'GVAC', 'SBGR'], 'initial_mass_kg': 185000, 'aircraft_type': 'B77W'},
    {'flight_id': 'BA404', 'origin_airport': 'EGLL', 'destination_airport': 'HKJK', 'waypoints': ['EGLL', 'LIRF', 'HECA', 'HKJK'], 'initial_mass_kg': 160000, 'aircraft_type': 'A359'},
    {'flight_id': 'LH505', 'origin_airport': 'EDDF', 'destination_airport': 'RKSI', 'waypoints': ['EDDF', 'EPWA', 'UWWW', 'RKSI'], 'initial_mass_kg': 190000, 'aircraft_type': 'B748'},
    {'flight_id': 'AF606', 'origin_airport': 'LFPG', 'destination_airport': 'MMMX', 'waypoints': ['LFPG', 'CYYZ', 'KIAH', 'MMMX'], 'initial_mass_kg': 170000, 'aircraft_type': 'B78X'},
    {'flight_id': 'SQ707', 'origin_airport': 'WSSS', 'destination_airport': 'NZAA', 'waypoints': ['WSSS', 'YPDN', 'YSSY', 'NZAA'], 'initial_mass_kg': 165000, 'aircraft_type': 'A359'}
]
AIRPORT_COORDS = {'KJFK': (40.64, -73.78), 'KSFO': (37.62, -122.37), 'KORD': (41.98, -87.90), 'KLAX': (33.94, -118.41), 'EGLL': (51.47, -0.45), 'CYUL': (45.47, -73.74), 'EIDW': (53.42, -6.27), 'KATL': (33.64, -84.43), 'RJTT': (35.55, 139.78), 'KSEA': (47.45, -122.31), 'PANC': (61.17, -149.99), 'EDDF': (50.03, 8.57), 'ZSPD': (31.14, 121.80), 'UUEE': (55.97, 37.41), 'UNNT': (55.01, 82.94), 'YSSY': (-33.95, 151.18), 'KDFW': (32.89, -97.04), 'NFFN': (-17.75, 177.44), 'OMDB': (25.25, 55.36), 'SBGR': (-23.43, -46.47), 'HBEG': (29.98, 32.71), 'GVAC': (-16.05, 22.82), 'HKJK': (-1.32, 36.93), 'LIRF': (41.80, 12.24), 'HECA': (30.12, 31.41), 'RKSI': (37.46, 126.44), 'EPWA': (52.17, 20.97), 'UWWW': (54.28, 48.23), 'LFPG': (49.01, 2.55), 'MMMX': (19.44, -99.07), 'CYYZ': (43.68, -79.63), 'KIAH': (29.98, -95.34), 'WSSS': (1.36, 103.99), 'NZAA': (-37.01, 174.79), 'YPDN': (-12.41, 130.87)}
AIRPORT_CITY_NAMES = {'KJFK': 'New York', 'KSFO': 'San Francisco', 'KORD': 'Chicago', 'KLAX': 'Los Angeles', 'EGLL': 'London', 'CYUL': 'Montreal', 'EIDW': 'Dublin', 'KATL': 'Atlanta', 'RJTT': 'Tokyo', 'KSEA': 'Seattle', 'PANC': 'Anchorage', 'EDDF': 'Frankfurt', 'ZSPD': 'Shanghai', 'UUEE': 'Moscow', 'UNNT': 'Novosibirsk', 'YSSY': 'Sydney', 'KDFW': 'Dallas', 'NFFN': 'Nadi', 'OMDB': 'Dubai', 'SBGR': 'Sao Paulo', 'HBEG': 'Alexandria', 'GVAC': 'Amilcar Cabral', 'HKJK': 'Nairobi', 'LIRF': 'Rome', 'HECA': 'Cairo', 'RKSI': 'Seoul', 'EPWA': 'Warsaw', 'UWWW': 'Ulyanovsk', 'LFPG': 'Paris', 'MMMX': 'Mexico City', 'CYYZ': 'Toronto', 'KIAH': 'Houston', 'WSSS': 'Singapore', 'NZAA': 'Auckland', 'YPDN': 'Darwin'}

# Section 3: Core Logic and Scientific Calculation Functions
def haversine(lat1, lon1, lat2, lon2):
    """Calculates the great-circle distance between two points on Earth in nautical miles."""
    R = 3440.1  # Earth radius in nautical miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def calculate_fuel_burn(aircraft_type, mass_kg, altitude_ft, distance_nm, temperature_isa_dev=0):
    """
    Calculates the fuel burn for a given flight segment using the OpenAP library.
    OpenAP provides scientifically validated aircraft performance models.
    """
    try:
        ff = FuelFlow(ac=aircraft_type, mass=mass_kg)
        # The enroute method calculates the fuel consumed over a specific distance and altitude.
        fuel_burn_kg = ff.enroute(alt=altitude_ft, dist=distance_nm, temp_dev=temperature_isa_dev)
        return fuel_burn_kg[0]
    except Exception:
        # If the library fails for a specific set of parameters, return infinity
        # to ensure this path is not chosen by the optimization algorithm.
        return float('inf')

def a_star_search(waypoints, aircraft_type, initial_mass_kg, weather_data):
    """
    Finds the optimal path (altitude profile) through the flight plan using the A* search algorithm.
    This function explores different altitude changes at each waypoint to find the route
    that consumes the least amount of fuel.
    """
    # The start node includes the first waypoint, a starting altitude, waypoint index, mass, and the initial path.
    start_node = (waypoints[0], 35000, 0, initial_mass_kg, [('start', 35000, 0, initial_mass_kg)])
    
    # The open_set is a priority queue that stores nodes to visit, prioritized by their cost.
    open_set = [(0, start_node)]
    
    # g_scores store the cost (total fuel burned) to get from the start node to the current node.
    g_scores = { (waypoints[0], 35000): 0 }
    
    while open_set:
        _, current_node = heapq.heappop(open_set)
        current_waypoint, current_alt, wp_idx, current_mass, path = current_node

        # If we have reached the last waypoint, we have found a complete path.
        if wp_idx == len(waypoints) - 1:
            return path, g_scores.get((current_waypoint, current_alt), float('inf'))

        # Explore possible next altitudes: climb, cruise, or descend.
        for alt_change in [-2000, 0, 2000]:
            next_alt = current_alt + alt_change
            # Ensure the next altitude is within a valid flight level range.
            if not (29000 <= next_alt <= 41000):
                continue
            
            # Move to the next waypoint in the flight plan.
            next_wp_idx = wp_idx + 1
            next_waypoint = waypoints[next_wp_idx]
            lat1, lon1 = AIRPORT_COORDS[current_waypoint]
            lat2, lon2 = AIRPORT_COORDS[next_waypoint]
            distance_nm = haversine(lat1, lon1, lat2, lon2)

            # Get weather data for the next segment.
            temp_dev = weather_data.get(next_waypoint, {}).get(next_alt, 0)
            
            # Calculate the cost (fuel burn) for this segment.
            fuel_burn = calculate_fuel_burn(aircraft_type, current_mass, next_alt, distance_nm, temp_dev)
            if fuel_burn == float('inf'): continue

            # The new g_score is the cost to the previous node plus the cost of the current segment.
            new_g_score = g_scores.get((current_waypoint, current_alt), float('inf')) + fuel_burn
            
            # If we've found a cheaper path to this next node, record it.
            if new_g_score < g_scores.get((next_waypoint, next_alt), float('inf')):
                g_scores[(next_waypoint, next_alt)] = new_g_score
                next_mass = current_mass - fuel_burn
                new_path = path + [(next_waypoint, next_alt, round(fuel_burn, 2), round(next_mass, 2))]
                
                # Heuristic (h_score): An estimate of the cost to get from the current node to the end.
                # Here, we use a simple heuristic based on remaining distance.
                h_score = (len(waypoints) - 1 - next_wp_idx) * 2000 # Simplified estimate
                
                # The f_score is the total estimated cost of the path through this node (g_score + h_score).
                # The priority queue uses this f_score to decide which node to explore next.
                f_score = new_g_score + h_score
                heapq.heappush(open_set, (f_score, (next_waypoint, next_alt, next_wp_idx, next_mass, new_path)))
                
    # If the loop finishes and no path was found, return None.
    return None, float('inf')

# Section 4: Agent Tools
# These functions are decorated with `@tool` to make them available to the Strands Agent.
@tool
def get_flight_plan(flight_id: str) -> dict:
    """Retrieves a specific flight plan from the internal database based on its flight_id."""
    for plan in ALL_FLIGHT_PLANS:
        if plan['flight_id'] == flight_id:
            return plan
    return {"error": f"Flight plan for {flight_id} not found."}

@tool
def get_weather_for_route(waypoints: list) -> dict:
    """Fetches weather data (temperature deviation from ISA) for a list of waypoints."""
    weather_data = {}
    for wp in waypoints:
        lat, lon = AIRPORT_COORDS.get(wp, (None, None))
        if not lat: continue
        
        # Using open-meteo.com for free weather forecast data.
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m&forecast_days=1"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Simplified model: Using a single temperature reading as a proxy for deviation.
                # A more complex model would fetch temperature at different altitudes (pressure levels).
                temp_c = data.get('hourly', {}).get('temperature_2m', [15])[0]
                isa_deviation = temp_c - 15 
                weather_data[wp] = {alt: isa_deviation for alt in range(29000, 41001, 2000)}
        except requests.exceptions.RequestException as e:
            print(f"Warning: Could not fetch weather for {wp}. Error: {e}")
            
    return weather_data

@tool
def run_fuel_optimization(flight_plan: dict, weather_data: dict) -> dict:
    """
    Executes the A* search algorithm to find the most fuel-efficient route and calculates savings
    by comparing it against a baseline route at a constant altitude.
    """
    waypoints = flight_plan['waypoints']
    aircraft_type = flight_plan['aircraft_type']
    initial_mass_kg = flight_plan['initial_mass_kg']

    # First, calculate a baseline fuel consumption by flying at a constant 35,000 ft.
    baseline_fuel = 0
    current_mass = initial_mass_kg
    for i in range(len(waypoints) - 1):
        wp1, wp2 = waypoints[i], waypoints[i+1]
        lat1, lon1 = AIRPORT_COORDS[wp1]
        lat2, lon2 = AIRPORT_COORDS[wp2]
        dist = haversine(lat1, lon1, lat2, lon2)
        fuel_segment = calculate_fuel_burn(aircraft_type, current_mass, 35000, dist, 0)
        baseline_fuel += fuel_segment
        current_mass -= fuel_segment

    # Second, run the A* search to find the truly optimal path.
    optimized_path, optimized_fuel = a_star_search(waypoints, aircraft_type, initial_mass_kg, weather_data)
    
    if optimized_path:
        return {
            "flight_id": flight_plan['flight_id'],
            "baseline_fuel_kg": round(baseline_fuel, 2),
            "optimized_fuel_kg": round(optimized_fuel, 2),
            "fuel_saved_kg": round(baseline_fuel - optimized_fuel, 2),
            "optimized_route": optimized_path,
            "rationale": "The optimized route adjusts altitudes based on weather and aircraft weight to minimize fuel consumption at each segment."
        }
    else:
        return {"error": "Optimization failed to find a valid path."}

@tool
def publish_recommendation(optimization_result: dict) -> str:
    """Publishes the final optimization recommendation to an AWS SQS queue for downstream systems."""
    try:
        sqs_queue_url = os.getenv("SQS_OUTPUT_QUEUE_URL")
        if not sqs_queue_url:
            return "Error: SQS_OUTPUT_QUEUE_URL is not configured in the .env file."
            
        sqs = boto3.client('sqs', region_name=os.getenv("AWS_REGION", "us-east-1"))
        sqs.send_message(
            QueueUrl=sqs_queue_url,
            MessageBody=json.dumps(optimization_result)
        )
        return f"Successfully published recommendation for flight {optimization_result.get('flight_id')} to SQS."
    except Exception as e:
        return f"Error publishing to SQS: {str(e)}"

# Section 5: The System Prompt
# This master prompt is the agent's primary instruction set. It guides the agent on how to
# orchestrate the tools in the correct sequence to achieve its goal.
SYSTEM_PROMPT = """
You are an expert AI agent specializing in airline fuel optimization. Your goal is to find the most fuel-efficient flight path for a given flight ID.

Follow this workflow precisely and without deviation:
1.  Use the `get_flight_plan` tool with the user-provided flight ID to retrieve the flight's details.
2.  Using the `waypoints` from the flight plan, call the `get_weather_for_route` tool to fetch the relevant weather data for the entire route.
3.  With both the complete flight plan and the full weather data, execute the `run_fuel_optimization` tool to calculate the optimal route and fuel savings.
4.  Finally, take the complete result from the optimization and publish it using the `publish_recommendation` tool.
5.  After publishing, present a concise summary of the results to the user, including baseline fuel, optimized fuel, and total savings.
"""

# Section 6: Main Execution Block
def main():
    """
    The main entry point for the script. This function handles parsing command-line
    arguments, initializing the agent, and running the optimization workflow.
    """
    # argparse is the standard way to create command-line interfaces in Python.
    parser = argparse.ArgumentParser(
        description="Run the Fuel Optimization Agent for a specific flight.",
        formatter_class=argparse.RawTextHelpFormatter # For better help text formatting
    )
    parser.add_argument(
        "flight_id",
        type=str,
        help="The ID of the flight to optimize (e.g., LH505, UA123)."
    )
    args = parser.parse_args()
    flight_id_to_optimize = args.flight_id

    # Crucial check: Verify that AWS credentials were successfully loaded from the .env file.
    if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("\n❌ ERROR: AWS credentials not found.")
        print("Please ensure you have a .env file in the same directory with your")
        print("AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION.\n")
        return

    print(f"--- Credentials loaded. Initializing Agent for Flight: {flight_id_to_optimize} ---")
    
    try:
        # Initialize the Strands Agent, providing the Bedrock model ID, the system prompt,
        # and the list of tools it is allowed to use.
        agent = Agent(
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            system_prompt=SYSTEM_PROMPT,
            tools=[get_flight_plan, get_weather_for_route, run_fuel_optimization, publish_recommendation]
        )

        # The initial prompt to kick off the agent's workflow.
        prompt = f"Please begin the optimization process for flight {flight_id_to_optimize}."
        print(f"--- Sending Prompt to Agent: '{prompt}' ---\n")

        # Calling the agent with the prompt. The agent will now follow the system prompt
        # and use its tools to get the answer.
        final_response = agent(prompt)

        print("\n--- Agent's Final Summary Report ---")
        print(final_response)
        print("\n--- End-to-End Workflow Complete ---")

    except Exception as e:
        # Catch-all for any other errors during agent execution.
        print(f"\n❌ An unexpected error occurred: {e}")
        print("Please check the following:")
        print("1. Your AWS credentials and IAM permissions for Bedrock and SQS.")
        print("2. Your internet connection.")
        print("3. That you have granted access to 'anthropic.claude-3-sonnet' in the Bedrock console.")

# This is the standard Python entry point guard.
# The code inside this block will only run when the script is executed directly
# (e.g., `python standalone_optimizer.py`), not when it's imported as a module.
if __name__ == "__main__":
    main()
