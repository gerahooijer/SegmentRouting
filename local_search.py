from collections import defaultdict
from read_input import get_link_id
import time

def calculate_flow(demand, waypoint, timestep, edge_flows, links, link_util):
    volume = demand['v'][timestep]

    if waypoint is None or waypoint == demand['s'] or waypoint == demand['t']:
        flow = edge_flows[demand['s'], demand['t']]
        for (u, v), percentage in flow.items():
            link_id = get_link_id(u, v)
            link_util[link_id] += percentage * volume / links[link_id].capacity
    else:
        flow_1 = edge_flows[demand['s'], waypoint]
        flow_2 = edge_flows[waypoint, demand['t']]
        for (u, v), percentage in flow_1.items():
            link_id = get_link_id(u, v)
            link_util[link_id] += percentage * volume / links[link_id].capacity
        for (u, v), percentage in flow_2.items():
            link_id = get_link_id(u, v)
            link_util[link_id] += percentage * volume / links[link_id].capacity

    return link_util

def compute_mlu_from_percentages(edge_flows, demands, links, waypoints, timestep):
    worst = 0
    link_util = defaultdict(float)
    for demand_id, demand in enumerate(demands):
        w = waypoints[demand_id][timestep]
        link_util= calculate_flow(demand, w, timestep, edge_flows, links, link_util)
    if link_util:
        worst = max(worst, max(link_util.values()))

    return worst, link_util

def update_mlu_percentages(edge_flows, demand, old_w, new_w, links, timestep, link_util):
    old_flow = calculate_flow(demand, old_w, timestep, edge_flows, links, link_util= defaultdict(float))
    new_flow = calculate_flow(demand, new_w, timestep, edge_flows, links, link_util= defaultdict(float))
    update_util = link_util.copy()
    for link_id in old_flow:
        update_util[link_id] -= old_flow[link_id]
    for link_id in new_flow:
        update_util[link_id] += new_flow[link_id]
    return max(update_util.values()), update_util

def segment_path(s, t, waypoint):
    if waypoint is None or waypoint == s or waypoint == t:
        return [(s, t)]
    return [(s, waypoint), (waypoint, t)]

def calculate_changing_cost (s, t, old_w, new_w):
    seg_1 = set(segment_path(s, t, old_w))
    seg_2 = set(segment_path(s, t, new_w))
    return len(seg_1.symmetric_difference(seg_2))

def local_search_precomputed_fg(demands, waypoints, edge_flow_all, links, num_nodes,
                                 current_mlu, link_util, timestep, prev_waypoints=None, 
                                 budget=None, time_limit=None, start_time=None):
    curr_link_util = (link_util).copy()

    #Run LS until no improvements found anymore
    improved = True
    while improved:
        if time_limit and (time.time() - start_time) > time_limit:
            break
        improved = False
        for demand_id, demand in enumerate(demands):
            s = demand['s']
            t = demand['t']
            start_w = waypoints[demand_id][timestep]
            current_w = waypoints[demand_id][timestep]
            changing_cost = 0

            # Only try changing demands that flow through heavily loaded links
            flow = calculate_flow(demand, current_w, timestep, edge_flow_all, links, defaultdict(float))
            if not any(curr_link_util.get(link_id, 0) > 0.5 for link_id in flow):
                continue

            candidates = [None] + [n for n in range(num_nodes) if n != current_w]
            for new_w in candidates:
                cost = 0
                #If there is a budget, calculate the cost of changing the waypoints
                if budget is not None and prev_waypoints is not None:
                    # Calculate cost
                    cost = calculate_changing_cost(s, t, current_w, new_w)
                    if budget - cost < 0: #If it does not fit within the budget, skip
                        continue

                #Compute the mlu for the new waypoint
                new_mlu, updated_link_util = update_mlu_percentages(edge_flow_all, demand, current_w,
                                                new_w, links, timestep, curr_link_util)

                if new_mlu < current_mlu:
                    current_mlu = new_mlu
                    current_w = new_w
                    waypoints[demand_id][timestep] = new_w
                    improved = True
                    curr_link_util = updated_link_util
                    if budget:
                        budget = budget + changing_cost - cost
                        changing_cost = cost
                        print("for demand", demand_id, "changed from", start_w, "to", current_w, "costs", changing_cost)
                        print("\t new budget = ", budget)

    return waypoints, curr_link_util, current_mlu

def local_search_bottleneck(demands, waypoints, edge_flow_all, links, num_nodes, 
                             current_mlu, link_util, timestep):
    improved = True
    while improved:
        improved = False
        
        # Find bottleneck link
        bottleneck_link = max(link_util, key=link_util.get)
        
        # Find all demands flowing through bottleneck
        bottleneck_demands = []
        for demand_id, demand in enumerate(demands):
            w = waypoints[demand_id][timestep]
            flow = calculate_flow(demand, w, timestep, edge_flow_all, links, defaultdict(float))
            if bottleneck_link in flow and flow[bottleneck_link] > 0:
                bottleneck_demands.append(demand_id)
        
        # Evaluate each bottleneck demand independently against original link_util
        best_changes = {}
        for demand_id in bottleneck_demands:
            demand = demands[demand_id]
            current_w = waypoints[demand_id][timestep]
            candidates = [None] + [n for n in range(num_nodes) if n != current_w]
            for new_w in candidates:
                new_mlu, _ = update_mlu_percentages(edge_flow_all, demand,
                                 current_w, new_w, links, timestep, link_util)
                if new_mlu < current_mlu:
                    best_changes[demand_id] = new_w
                    break
        
        # Apply all changes at once
        if best_changes:
            temp_waypoints = [list(w) for w in waypoints]
            for demand_id, new_w in best_changes.items():
                temp_waypoints[demand_id][timestep] = new_w
            
            # Measure combined effect
            temp_mlu, temp_util = compute_mlu_from_percentages(edge_flow_all, demands, links, temp_waypoints, timestep)
            
            if temp_mlu < current_mlu:
                current_mlu = temp_mlu
                waypoints = temp_waypoints
                link_util = temp_util
                improved = True
    
    return waypoints, link_util, current_mlu