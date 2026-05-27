from collections import defaultdict

from read_input import read_input, generate_adjacency_lists, Link, get_link_id
from forwarding_graphs import find_forwarding_graph, ecmp_calculation, compute_edge_flow
import time
import random
from generate_output_file import output_file

random.seed(2705)

if __name__ == '__main__':
    #Read in the instance, and generate the adjacency list
    instance = '01'
    input_graph, scenario, traffic_matrix = read_input(instance)
    graph, links = generate_adjacency_lists(input_graph)
    num_time_slots, demands = traffic_matrix

    start_time = time.time()

    """Pick random waypoints"""
    num_nodes = len(graph)
    waypoints = [[None] * num_time_slots for _ in range(len(demands))]

    for demand_id, demand in enumerate(demands):
        s = demand['s']
        t = demand['t']
        for timestep in range(num_time_slots):
            w = random.choice([n for n in range(num_nodes) if n != s and n != t])
            waypoints[demand_id][timestep] = w
            print("Trying waypoint", w, "for demand", demand_id, "at timestep", timestep)

    """"Compute edge flows using current waypoints"""
    edge_flows = defaultdict()
    for demand_id, demand in enumerate(demands):
        source = demand['s']
        target = demand['t']
        for timestep in range(num_time_slots):
            volume = demand['v'][timestep]
            w = waypoints[demand_id][timestep]
            edge_flow = compute_edge_flow(source, target, w, volume, graph, links)
            edge_flows[(demand_id, timestep)] = edge_flow  

    """"Calculate the flow over each edge, for every timestep"""
    link_load =[[0 for _ in enumerate(links)]for _ in range(num_time_slots)]
    link_utilization =[[0 for _ in enumerate(links)]for _ in range(num_time_slots)]

    for timestep in range(num_time_slots):
        for demand_id, demand in enumerate(demands):
            edge_flow = edge_flows[(demand_id, timestep)]
            for (u,v), load in edge_flow.items():
                link_id = get_link_id(u, v)
                link_load[timestep][link_id] += load
                link_utilization[timestep][link_id] += load / links[link_id].capacity

    for timestep in range(num_time_slots):
        print("for time step", timestep, "link loads are:", link_load[timestep])
        print("for time step", timestep, "link utilizations are:", link_utilization[timestep])
        print("the highest utilization is", max(link_utilization[timestep]), "\n")

        print("max timestep 0:", max(link_utilization[0]))
        print("max timestep 1:", max(link_utilization[1]))
        overutilised = [(i, link_utilization[timestep][i]) for i in range(len(links)) if link_utilization[timestep][i] > 1.0]
        if overutilised:
            print("overutilised links:", overutilised)
        else:
            print("no overutilised links")

    end_time = time.time()
    print(round(end_time - start_time, 5), "seconds")