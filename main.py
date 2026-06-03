from collections import defaultdict

from pip._internal.resolution.resolvelib import candidates

import generate_output_file
from read_input import read_input, generate_adjacency_lists, Link, get_link_id
from forwarding_graphs import get_all_forwarding_graphs
import time
import random
from generate_output_file import output_file
from local_search import compute_mlu_from_percentages, local_search_precomputed_fg, local_search_precomputed_fg_multiple_moves, get_excluded_nodes
from removed_links import remove_downed_links

random.seed(2705)

if __name__ == '__main__':
    #Read in the instance, and generate the adjacency list
    instance = ('14')
    input_graph, scenario, traffic_matrix = read_input(instance)
    graph, links = generate_adjacency_lists(input_graph)
    num_time_slots, demands = traffic_matrix

    overall_start_time = time.time()

    max_segments, budget_list, interventions = scenario
    budget_t1 = budget_list[0]['value']
    graph_t1 = remove_downed_links(graph, interventions, 1)

    #Calculate forwarding graphs and edge flows for both timesteps
    e_flow_t0, nodes_in_fg_0  = get_all_forwarding_graphs(graph, links, len(graph))
    e_flow_t1, nodes_in_fg_1  = get_all_forwarding_graphs(graph_t1, links, len(graph_t1))

    """Random restarts"""
    best_waypoints = None
    best_mlu_0 = float('inf')
    num_nodes = len(graph)

    for restart in range(200):

        waypoints = [[[demand['s']] + [demand['t']]] * num_time_slots for demand in demands]
        exclusion_layer = 0

        for demand_id, demand in enumerate(demands):
            s = demand['s']
            t = demand['t']

            fg_nodes = set(nodes_in_fg_0[(s, t)])
            excluded = get_excluded_nodes(fg_nodes, graph, exclusion_layer)
            candidates = [n for n in range(num_nodes) if n not in excluded and n != s and n != t]

            if not candidates:
                candidates = [n for n in range(num_nodes) if n not in fg_nodes and n != s and n != t]

            if candidates:
                w = random.choice(candidates)
                waypoints[demand_id][0] = [s, w, t]  # schoon pad: s → w → t
            else:
                waypoints[demand_id][0] = [s, t]  # geen waypoint mogelijk

        #Compute MLU for current demands and waypoints
        current_mlu, link_util = compute_mlu_from_percentages(e_flow_t0, demands, links, waypoints, timestep = 0)

        start_time_ls = time.time()
        #Run local search, return waypoints and new MLU
        waypoints, new_link_util, new_mlu = local_search_precomputed_fg_multiple_moves(graph, demands, waypoints, e_flow_t0,
                                                links, num_nodes, current_mlu, link_util, timestep=0, exclusion_layer=1)

        end_time_ls = time.time()
        #print("time spent in LS:", round(end_time_ls - start_time_ls, 5), "seconds")

        #print("\nMLU before local search", current_mlu)
        #print("MLU after local search", new_mlu)

        if new_mlu < best_mlu_0:
            best_mlu_0 = new_mlu
            best_waypoints = [list(w) for w in waypoints]
            best_util = new_link_util
            print("Restart", restart + 1, ": new best MLU = ", best_mlu_0)

    print("Waypoints after timestep 0", best_waypoints)
    print("Running local search for timestep", 1, "with budget", budget_t1)
    print("Links removed at t=1:", [intervention['links'] for intervention in interventions if intervention['t'] == 1])

    """Timestep 1 starting from best t=0 solution"""
    waypoints_t1 = [[None] * num_time_slots for _ in range(len(demands))]
    for d, (_,_) in enumerate(best_waypoints):
        waypoints_t1[d][0] = best_waypoints[d][0]
        waypoints_t1[d][1] = best_waypoints[d][0]

    # Compute MLU for current demands and waypoints
    current_mlu_1, link_util_1 = compute_mlu_from_percentages(e_flow_t1, demands, links, waypoints_t1, timestep=1)

    waypoints, new_link_util_t1, new_mlu_1 = local_search_precomputed_fg_multiple_moves(graph, demands, waypoints_t1, e_flow_t1,
                                                links, num_nodes, current_mlu_1, link_util_1,
                                                timestep=1, prev_waypoints=best_waypoints, budget=budget_t1, exclusion_layer=0)
    end_time = time.time()
    print(waypoints)
    """"Calculate the flow over each edge, for every timestep"""
    link_load =[[0 for _ in enumerate(links)]for _ in range(num_time_slots)]
    link_utilization =[[0 for _ in enumerate(links)]for _ in range(num_time_slots)]

    print("\nfor timestep 0", best_util)
    print("MLU", round(best_mlu_0, 4))
    print("for timestep 1", new_link_util_t1)
    print("MLU", round(new_mlu_1, 4))

    output_file(demands, num_time_slots, instance, waypoints)

    final_end_time = time.time()
    print(round(final_end_time - overall_start_time, 5), "seconds")