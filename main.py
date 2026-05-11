from collections import defaultdict

from read_input import read_input, generate_adjacency_lists, Link, get_link_id
from forwarding_graphs import find_forwarding_graph, ecmp_calculation
import time
from generate_output_file import output_file

if __name__ == '__main__':
    #Read in the instance, and generate the adjacency list
    instance = '21'
    input_graph, scenario, traffic_matrix = read_input(instance)
    graph, links = generate_adjacency_lists(input_graph)
    num_time_slots, demands = traffic_matrix

    start_time = time.time()

    """"Calculate the forwarding graph for every demand node pair and calculate the flow over each edge and node"""
    node_flows = defaultdict()
    edge_flows = defaultdict()
    for demand_id, demand in enumerate(demands):
        source = demand['s']
        target = demand['t']
        fw_graph, parents, nodes = find_forwarding_graph(source, target, graph, links)
        for timestep in range(num_time_slots):
            volume = demand['v'][timestep]
            node_flow, edge_flow = ecmp_calculation(source, parents, nodes, volume)
            node_flows[(demand_id, timestep)] = node_flow
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
        print("for times step", timestep, "link loads are:", link_load[timestep])
        print("for times step", timestep, "link utilizations are:", link_utilization[timestep])
        print("the highest utilization is", max(link_utilization[timestep]), "\n")



    end_time = time.time()
    print(round(end_time - start_time, 5), "seconds")