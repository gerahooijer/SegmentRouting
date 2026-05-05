import json

def output_file(demands, time_slots, instance, segments = False):
    data = {"srpaths": []}
    if not segments:
        for id, demand in enumerate(demands):
            for time in range(time_slots):
                waypoints = []
                output_data = {"d": id, "t": time, "w": waypoints}
                data["srpaths"].append(output_data)

    # Write to JSON file
    with open(f'setA/setA-{instance}-srpaths.json', 'w') as file:
        json.dump(data, file, indent=2, separators=(',', ': '))