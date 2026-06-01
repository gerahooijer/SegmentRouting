import json

def output_file(demands, time_slots, instance, waypoints):
    data = {"srpaths": []}
    for id, demand in enumerate(demands):
        for time in range(time_slots):
            num_waypoints = len(waypoints[id][time])
            waypoint = waypoints[id][time][1:num_waypoints-1]
            output_data = {"d": id, "t": time, "w": waypoint}
            data["srpaths"].append(output_data)

    # Write to JSON file
    with open(f'setA/setA-{instance}-srpaths.json', 'w') as file:
        json.dump(data, file, indent=2, separators=(',', ': '))