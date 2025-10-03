# -*- coding: utf-8 -*-
"""
Airline Fuel Optimization Agent - End-to-End Platform-Independent Script.

This script has been refactored to be callable from other modules,
such as an AWS Lambda handler, while retaining its command-line functionality.
"""
# --- Section 0: All Necessary Imports ---
import os
import json
import heapq
import math
import argparse
import sys
import pandas as pd
import boto3
import requests
from dotenv import load_dotenv
from strands import Agent, tool
from openap import FuelFlow

# --- Section 1: Environment and Configuration ---
load_dotenv()

# --- Section 2: Data Sources and Constants ---
WAYPOINT_COORDINATES = {
    'KJFK': (40.6413, -73.7781), 'KORD': (41.9742, -87.9073), 'KSFO': (37.6213, -122.3790),
    'KLAX': (33.9416, -118.4085), 'CYUL': (45.4706, -73.7408), 'EIDW': (53.4264, -6.2499), 'EGLL': (51.4700, -0.4543),
    'KATL': (33.6407, -84.4277), 'KSEA': (47.4480, -122.3088), 'PANC': (61.1744, -149.9983), 'RJTT': (35.5494, 139.7798),
    'EDDF': (50.0379, 8.5622), 'UUEE': (55.9726, 37.4146), 'UNNT': (55.0128, 82.6503), 'ZSPD': (31.1434, 121.8053),
    'YSSY': ( -33.9399, 151.1753), 'NFFN': (-17.7550, 177.4436), 'KDFW': (32.8998, -97.0403),
    'OMDB': (25.2532, 55.3657), 'HBEG': (11.5556, 43.1594), 'GVAC': (16.0633, -22.9461), 'SBGR': (-23.4356, -46.4731),
    'LIRF': (41.8003, 12.2389), 'HECA': (30.1219, 31.4056), 'HKJK': (-1.3192, 36.9278),
    'EPWA': (52.1657, 20.9671), 'UWWW': (53.4981, 49.2789), 'RKSI': (37.4611, 126.4407),
    'LFPG': (49.0097, 2.5479), 'CYYZ': (43.6777, -79.6248), 'KIAH': (29.9902, -95.3368), 'MMMX': (19.4363, -99.0721),
    'WSSS': (1.3644, 103.9915), 'NZAA': (-37.0082, 174.7917)
}
FLIGHT_LEVELS = [290, 310, 330, 350, 370, 390]

# --- Section 3: Core Logic and Helper Functions ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_fuel_burn(aircraft_type, mass_kg, altitude_ft, distance_km, tas_kts, temperature_c):
    ff = FuelFlow(ac=aircraft_type, pax=0)
    params = {'mass': mass_kg, 'alt': altitude_ft, 'tas': tas_kts, 'isa_dev': temperature_c - (15 - (altitude_ft / 1000 * 2))}
    fuel_flow_kg_s = ff.enroute(**params)
    time_hours = (distance_km / 1.852) / tas_kts
    return fuel_flow_kg_s * time_hours * 3600

def a_star_search(flight_plan, weather_data):
    start_node = (flight_plan['waypoints'][0], FLIGHT_LEVELS[3], flight_plan['initial_mass_kg'])
    open_set = [(0, start_node)]
    came_from = {}
    g_score = { (wp, fl): float('inf') for wp in flight_plan['waypoints'] for fl in FLIGHT_LEVELS }
    g_score[(start_node[0], start_node[1])] = 0
    mass_at_node = { (start_node[0], start_node[1]): flight_plan['initial_mass_kg'] }
    while open_set:
        _, current = heapq.heappop(open_set)
        current_wp, current_fl, current_mass = current[0], current[1], mass_at_node[(current[0], current[1])]
        if current_wp == flight_plan['destination_airport']:
            path, total_fuel = [], 0
            while (current_wp, current_fl) in came_from:
                prev_wp, prev_fl = came_from[(current_wp, current_fl)]
                path.append({'waypoint': current_wp, 'flight_level': current_fl})
                total_fuel += g_score[(current_wp, current_fl)] - g_score[(prev_wp, prev_fl)]
                current_wp, current_fl = prev_wp, prev_fl
            path.append({'waypoint': start_node[0], 'flight_level': start_node[1]})
            return list(reversed(path)), total_fuel
        current_wp_idx = flight_plan['waypoints'].index(current_wp)
        if current_wp_idx + 1 >= len(flight_plan['waypoints']): continue
        next_wp = flight_plan['waypoints'][current_wp_idx + 1]
        for next_fl in FLIGHT_LEVELS:
            lat1, lon1 = WAYPOINT_COORDINATES[current_wp]
            lat2, lon2 = WAYPOINT_COORDINATES[next_wp]
            distance_km = haversine(lat1, lon1, lat2, lon2)
            weather = weather_data.get(next_wp, {})
            temp_c, wind_speed_kts, tas_kts = weather.get('temperature_c', 15), weather.get('wind_speed_kts', 0), 450
            ground_speed_kts = tas_kts + wind_speed_kts
            fuel_burned = calculate_fuel_burn(flight_plan['aircraft_type'], current_mass, next_fl * 100, distance_km, ground_speed_kts, temp_c)
            tentative_g_score = g_score[(current_wp, current_fl)] + fuel_burned
            if tentative_g_score < g_score.get((next_wp, next_fl), float('inf')):
                came_from[(next_wp, next_fl)], g_score[(next_wp, next_fl)] = (current_wp, current_fl), tentative_g_score
                mass_at_node[(next_wp, next_fl)] = current_mass - fuel_burned
                heapq.heappush(open_set, (tentative_g_score, (next_wp, next_fl)))
    return None, float('inf')

# --- Section 4: Agent Tool Definitions ---
@tool
def get_flight_plan(flight_id: str) -> str:
    print(f"Tool 'get_flight_plan' called for flight_id: {flight_id}")
    try:
        df = pd.read_csv("flight_plans.csv")
        flight_plan = df[df['flight_id'] == flight_id].to_dict('records')
        if not flight_plan: return json.dumps({"error": f"Flight plan for '{flight_id}' not found."})
        fp = flight_plan[0]
        if isinstance(fp['waypoints'], str):
            fp['waypoints'] = [wp.strip() for wp in fp['waypoints'].strip('[]').replace("'", "").replace('"', '').split(',')]
        return json.dumps(fp)
    except FileNotFoundError: return json.dumps({"error": "The 'flight_plans.csv' file was not found."})
    except Exception as e: return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

@tool
def get_weather_for_route(waypoints: list[str]) -> str:
    print(f"Tool 'get_weather_for_route' called for waypoints: {waypoints}")
    weather_data = {}
    for wp in waypoints:
        lat, lon = WAYPOINT_COORDINATES.get(wp, (0,0))
        if lat == 0: continue
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get('current_weather', {})
            weather_data[wp] = {'temperature_c': data.get('temperature'), 'wind_speed_kts': data.get('windspeed') * 0.54}
        except requests.RequestException as e:
            print(f"Warning: Could not fetch weather for {wp}. Using defaults. Error: {e}")
            weather_data[wp] = {'temperature_c': 15, 'wind_speed_kts': 0}
    return json.dumps(weather_data)

@tool
def run_fuel_optimization(flight_plan: dict, weather_data: dict) -> str:
    print(f"Tool 'run_fuel_optimization' called for flight: {flight_plan.get('flight_id')}")
    baseline_mass, baseline_fuel = flight_plan['initial_mass_kg'], 0
    for i in range(len(flight_plan['waypoints']) - 1):
        wp1, wp2 = flight_plan['waypoints'][i], flight_plan['waypoints'][i+1]
        lat1, lon1 = WAYPOINT_COORDINATES[wp1]; lat2, lon2 = WAYPOINT_COORDINATES[wp2]
        distance_km = haversine(lat1, lon1, lat2, lon2)
        fuel_burned = calculate_fuel_burn(flight_plan['aircraft_type'], baseline_mass, 35000, distance_km, 450, 15)
        baseline_fuel += fuel_burned; baseline_mass -= fuel_burned
    optimized_path, optimized_fuel = a_star_search(flight_plan, weather_data)
    if optimized_path:
        return json.dumps({"status": "success", "baseline_fuel_kg": round(baseline_fuel), "optimized_fuel_kg": round(optimized_fuel), "fuel_saved_kg": round(baseline_fuel - optimized_fuel), "optimized_route": optimized_path})
    else: return json.dumps({"status": "error", "message": "Optimization failed to find a path."})

@tool
def publish_recommendation(flight_id: str, baseline_fuel_kg: int, optimized_fuel_kg: int, fuel_saved_kg: int, rationale: str, optimized_route: list) -> str:
    print(f"Tool 'publish_recommendation' called for flight: {flight_id}")
    try:
        sqs = boto3.client('sqs', region_name=os.getenv('AWS_DEFAULT_REGION'))
        queue_url = os.getenv('SQS_OUTPUT_QUEUE_URL')
        message_body = json.dumps({"flight_id": flight_id, "baseline_fuel_kg": baseline_fuel_kg, "optimized_fuel_kg": optimized_fuel_kg, "fuel_saved_kg": fuel_saved_kg, "rationale": rationale, "optimized_route": optimized_route})
        sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
        return json.dumps({"status": "success", "message": f"Recommendation for {flight_id} published to SQS."})
    except Exception as e:
        error_message = f"Failed to publish to SQS: {str(e)}"; print(f"ERROR: {error_message}")
        return json.dumps({"status": "error", "message": error_message})

# --- Section 5: System Prompt ---
SYSTEM_PROMPT = """You are an expert AI agent specializing in airline fuel optimization... Your final action is to call `publish_recommendation`.""" # Truncated for brevity

# --- Section 6: Refactored Agent Workflow ---
def run_agent_workflow(flight_id: str):
    """
    Encapsulates the agent execution logic to be called from different entry points.
    """
    # Verify that essential environment variables are set
    REQUIRED_VARS = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION', 'SQS_OUTPUT_QUEUE_URL']
    for var in REQUIRED_VARS:
        if not os.getenv(var):
            error_msg = f"FATAL ERROR: Environment variable '{var}' is not set."
            print(error_msg)
            return {"status": "error", "message": error_msg}

    print(f"--- Starting Agent Workflow for Flight: {flight_id} ---")
    try:
        agent = Agent(
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            system_prompt=SYSTEM_PROMPT,
            tools=[get_flight_plan, get_weather_for_route, run_fuel_optimization, publish_recommendation]
        )
        prompt = f"Please begin the optimization process for flight {flight_id}."
        print(f"--- Sending Prompt to Agent: '{prompt}' ---\n")
        final_response = agent(prompt)
        print("\n--- Agent's Final Summary Report ---")
        print(final_response)
        return {"status": "success", "response": final_response}
    except Exception as e:
        error_msg = f"An unhandled error occurred in agent workflow: {e}"
        print(f"\n--- ❌ {error_msg} ---")
        return {"status": "error", "message": error_msg}

# --- Section 7: Main Execution Block for Command-Line ---
def main():
    """Main function to run the agent from the command line."""
    parser = argparse.ArgumentParser(description="Run the Airline Fuel Optimization Agent.", epilog="Example: `python fuel_optimization_agent.py UA123`")
    parser.add_argument("flight_id", type=str, help="The ID of the flight to optimize (e.g., UA123, LH505).")
    args = parser.parse_args()
    run_agent_workflow(args.flight_id)
    print("\n--- Command-Line Workflow Complete ---")

if __name__ == "__main__":
    main()

