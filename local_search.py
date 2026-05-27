from collections import defaultdict
from read_input import get_link_id
from forwarding_graphs import compute_edge_flow

def compute_mlu_from_flows(edge_flows, links, num_time_slots):
    best = 0
    for timestep in range(num_time_slots):
        link_util = defaultdict(float)
        for (demand_id, ts), edge_flow in edge_flows.items():
            if ts != timestep:
                continue
            for (u, v), flow in edge_flow.items():
                link_id = get_link_id(u, v)
                link_util[link_id] += flow / links[link_id].capacity
        if link_util:
            best = max(best, max(link_util.values()))
    return best

def compute_mlu_single_timestep(edge_flows, links, timestep):
    link_util = defaultdict(float)
    for (demand_id, ts), edge_flow in edge_flows.items():
        if ts != timestep:
            continue
        for (u, v), flow in edge_flow.items():
            link_id = get_link_id(u, v)
            link_util[link_id] += flow / links[link_id].capacity
    return max(link_util.values()) if link_util else 0

def local_search_timestep(demands, waypoints, edge_flows, graph, links, num_nodes, num_time_slots, timestep, prev_waypoints=None, budget=None):
    current_mlu = compute_mlu_single_timestep(edge_flows, links, timestep)
    
    improved = True
    while improved:
        improved = False
        for demand_id, demand in enumerate(demands):
            s = demand['s']
            t = demand['t']
            current_w = waypoints[demand_id][timestep]
            volume = demand['v'][timestep]
            
            candidates = [None] + [n for n in range(num_nodes) if n != s and n != t and n != current_w]
            for new_w in candidates:
                
                if budget is not None and prev_waypoints is not None:
                    if new_w != prev_waypoints[demand_id][timestep]:
                        changes = sum(1 for d in range(len(demands)) 
                                     if waypoints[d][timestep] != prev_waypoints[d][timestep])
                        if changes >= budget:
                            continue
                
                # only recompute flow for this one demand
                new_flow = compute_edge_flow(s, t, new_w, volume, graph, links)
                old_flow = edge_flows[(demand_id, timestep)]
                edge_flows[(demand_id, timestep)] = new_flow
                
                new_mlu = compute_mlu_single_timestep(edge_flows, links, timestep)
                
                if new_mlu < current_mlu:
                    current_mlu = new_mlu
                    current_w = new_w
                    waypoints[demand_id][timestep] = new_w
                    improved = True
                else:
                    edge_flows[(demand_id, timestep)] = old_flow
    
    return waypoints, edge_flows    
