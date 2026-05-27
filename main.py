from collections import defaultdict
from read_input import read_input, generate_adjacency_lists, Link, get_link_id
from forwarding_graphs import compute_edge_flow
import time
import random
from generate_output_file import output_file
from local_search import local_search_timestep, compute_mlu_from_flows, compute_mlu_single_timestep
from removed_links import remove_downed_links

random.seed(2705)

if __name__ == '__main__':
    #Read in the instance, and generate the adjacency list
    instance = '01'
    input_graph, scenario, traffic_matrix = read_input(instance)
    graph, links = generate_adjacency_lists(input_graph)
    num_time_slots, demands = traffic_matrix

    start_time = time.time()

    max_segments, budget_list, interventions = scenario
    budget_t1 = budget_list[0]['value']
    graph_t1 = remove_downed_links(graph, interventions, 1)

    """Random restarts"""
    best_waypoints = None
    best_mlu = float('inf')
    for restart in range(5):

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
        
        print("MLU before local search:", compute_mlu_from_flows(edge_flows, links, num_time_slots))
        waypoints, edge_flows = local_search_timestep(demands, waypoints, edge_flows, graph, links, num_nodes, num_time_slots, timestep=0)
        print("MLU after local search:", compute_mlu_from_flows(edge_flows, links, num_time_slots))

        new_mlu = compute_mlu_from_flows(edge_flows, links, num_time_slots)
        if new_mlu < best_mlu:
            best_mlu = new_mlu
            best_waypoints = [list(w) for w in waypoints]
            best_edge_flows = dict(edge_flows)
            print("Restart", restart+1, ": new best MLU = ", best_mlu)

    print("Running local search for timestep", timestep, "with budget", budget_t1)
    print("Links removed at t=1:", [intervention['links'] for intervention in interventions if intervention['t'] == 1])

    """Timestep 1 starting from best t=0 solution"""
    waypoints = [list(w) for w in best_waypoints]
    edge_flows = dict(best_edge_flows)

    for demand_id, demand in enumerate(demands):
        source = demand['s']
        target = demand['t']
        volume = demand['v'][1]
        w = waypoints[demand_id][1]
        edge_flows[(demand_id, 1)] = compute_edge_flow(source, target, w, volume, graph_t1, links)
    print("MLU of t=1 before local search:", compute_mlu_single_timestep(edge_flows, links, 1))

    waypoints, edge_flows = local_search_timestep(
        demands, waypoints, edge_flows, graph_t1, links,
        num_nodes, num_time_slots, timestep=1,
        prev_waypoints=best_waypoints, budget=budget_t1
    )

    best_edge_flows = dict(edge_flows)  # update best_edge_flows with t=1 result

    """"Calculate the flow over each edge, for every timestep"""
    link_load =[[0 for _ in enumerate(links)]for _ in range(num_time_slots)]
    link_utilization =[[0 for _ in enumerate(links)]for _ in range(num_time_slots)]

    for timestep in range(num_time_slots):
        for demand_id, demand in enumerate(demands):
            edge_flow = best_edge_flows[(demand_id, timestep)]
            for (u,v), load in edge_flow.items():
                link_id = get_link_id(u, v)
                link_load[timestep][link_id] += load
                link_utilization[timestep][link_id] += load / links[link_id].capacity

    for timestep in range(num_time_slots):
        print("for time step", timestep, "link loads are:", link_load[timestep])
        print("for time step", timestep, "link utilizations are:", link_utilization[timestep])
        print("the highest utilization is", max(link_utilization[timestep]), "\n")

        """Check which links are overutilised"""
        overutilised = [(i, link_utilization[timestep][i]) for i in range(len(links)) if link_utilization[timestep][i] > 1.0]
        if overutilised:
            print("overutilised links:", overutilised)
        else:
            print("no overutilised links")

    end_time = time.time()
    print(round(end_time - start_time, 5), "seconds")
