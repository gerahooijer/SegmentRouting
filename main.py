from collections import defaultdict

from pip._internal.resolution.resolvelib import candidates

import generate_output_file
from read_input import read_input, generate_adjacency_lists, Link, get_link_id
from forwarding_graphs import get_all_forwarding_graphs
import time
import random
from generate_output_file import output_file
from local_search import compute_mlu_from_percentages, local_search_precomputed_fg, local_search_precomputed_fg_multiple_moves
from removed_links import remove_downed_links

random.seed(2705)

if __name__ == '__main__':
    #Read in the instance, and generate the adjacency list
    instance = ('01')
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

        """Pick random waypoints"""
        waypoints = [[[demand['s']]] * num_time_slots for demand in demands]
        for demand_id, demand in enumerate(demands):
            s = demand['s']
            t = demand['t']

            #Candidates for waypoint are all nodes on the FG and all nodes adjacent to nodes on the FG
            #print(nodes_in_fg_0[(s,t)])
            adjacent = set()
            for node in nodes_in_fg_0[(s,t)]:
                adjacent.update(graph[node].keys())
                #print(graph[node].keys())
            candidates = [n for n in adjacent if n != s and n!= t]
            #print("for ", s, "and", t, "cand", candidates)

            used = set()
            number_waypoints = random.randint(0, max_segments - 2)
            for _ in range(1):
                if not candidates:
                    break
                w = random.choice(candidates)
                used.add(w)
                waypoints[demand_id][0].append(w)
            waypoints[demand_id][0].append(t)

        #Compute MLU for current demands and waypoints
        current_mlu, link_util = compute_mlu_from_percentages(e_flow_t0, demands, links, waypoints, timestep = 0)

        start_time_ls = time.time()
        #Run local search, return waypoints and new MLU
        waypoints, new_link_util, new_mlu = local_search_precomputed_fg_multiple_moves(graph, demands, waypoints, e_flow_t0,
                                                links, num_nodes, current_mlu, link_util, timestep=0)

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
                                                timestep=1, prev_waypoints=best_waypoints, budget=budget_t1)
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