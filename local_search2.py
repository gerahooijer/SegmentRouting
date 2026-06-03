import random
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

def calculate_flow_multiple_waypoints(s1, s2, volume, timestep, edge_flows, links, link_util):
    flow = edge_flows[s1, s2]
    for (u, v), percentage in flow.items():
        link_id = get_link_id(u, v)
        link_util[link_id] += percentage * volume / links[link_id].capacity
    return link_util


def compute_mlu_from_percentages(edge_flows, demands, links, waypoints, timestep):
    worst = 0
    link_util = defaultdict(float)
    for demand_id, demand in enumerate(demands):
        volume = demand['v'][timestep]
        waypoint = waypoints[demand_id][timestep]
        for idx in range(len(waypoint)-1):
            s1 = waypoint[idx]
            s2 = waypoint[idx+1]
            link_util = calculate_flow_multiple_waypoints(s1, s2, volume, timestep, edge_flows, links, link_util)
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

def update_mlu_percentages_multiple_waypoints(edge_flows, demand, old_w, new_w, links, timestep, link_util):
    volume = demand['v'][timestep]
    update_util = link_util.copy()

    seg_old = set(segment_path(demand['s'], demand['t'], old_w))
    seg_new = set(segment_path(demand['s'], demand['t'], new_w))

    old_segments = seg_old - seg_new
    new_segments = seg_new - seg_old

    old_flow = defaultdict(float)
    new_flow = defaultdict(float)
    for (u, v) in old_segments:
        old_flow = calculate_flow_multiple_waypoints(u, v, volume, timestep, edge_flows, links, old_flow)
    for (u,v) in new_segments:
        new_flow = calculate_flow_multiple_waypoints(u, v, volume, timestep, edge_flows, links, new_flow)

    for link_id in old_flow:
        update_util[link_id] -= old_flow[link_id]
    for link_id in new_flow:
        update_util[link_id] += new_flow[link_id]

    return max(update_util.values()), update_util


def segment_path(s, t, waypoint):
    segment = []
    for idx in range(len(waypoint)-1):
        segment.append((waypoint[idx], waypoint[idx+1]))
    return segment

def calculate_changing_cost (s, t, old_w, new_w):
    seg_1 = set(segment_path(s, t, old_w))
    seg_2 = set(segment_path(s, t, new_w))
    return len(seg_1.symmetric_difference(seg_2))

def add_waypoint(current_mlu, demand, current_w, new_w, link_util,
                                                        timestep, edge_flows, links):
    best_mlu = current_mlu
    best_w = current_w.copy()
    best_util = link_util.copy()

    #Add node at all possible positions and pick the best
    for idx in range(1, len(current_w)):
        update_util = link_util.copy()
        temp_w = current_w.copy()
        temp_w.insert(idx, new_w)

        new_mlu, updated_link_util = update_mlu_percentages_multiple_waypoints(edge_flows, demand, best_w,
                                                                               temp_w, links, timestep, update_util)
        if new_mlu < best_mlu:
            best_mlu = new_mlu
            best_w = temp_w.copy()
            best_util = updated_link_util
            #print("succesfull addition")

    return best_w, best_mlu, best_util


def remove_waypoint(current_mlu, demand, current_w, link_util, timestep, edge_flows, links):
    best_mlu = current_mlu
    best_w = current_w.copy()
    best_util = link_util.copy()

    # Try removing each waypoint (except source and destination)
    if len(current_w) <= 2:
        return best_w, best_mlu, best_util  # Cannot remove if only source and destination

    for idx in range(1, len(current_w) - 1):
        update_util = link_util.copy()
        temp_w = current_w.copy()
        removed_waypoint = temp_w.pop(idx)  # Remove waypoint at index idx

        new_mlu, updated_link_util = update_mlu_percentages_multiple_waypoints(
            edge_flows, demand, current_w, temp_w, links, timestep, update_util
        )

        if new_mlu < best_mlu:
            best_mlu = new_mlu
            best_w = temp_w.copy()
            best_util = updated_link_util
            #print("succesfull removal")

    return best_w, best_mlu, best_util


def switch_waypoint(current_mlu, demand, current_w, new_w, link_util, timestep, edge_flows, links):
    best_mlu = current_mlu
    best_w = current_w.copy()
    best_util = link_util.copy()

    # Try switching new_w at all possible positions (except source and destination)
    for idx in range(1, len(current_w) - 1):
        update_util = link_util.copy()
        temp_w = current_w.copy()
        temp_w[idx] = new_w  # Replace waypoint at index idx with new_w
        new_mlu, updated_link_util = update_mlu_percentages_multiple_waypoints(
            edge_flows, demand, current_w, temp_w, links, timestep, update_util
        )

        if new_mlu < best_mlu:
            best_mlu = new_mlu
            best_w = temp_w.copy()
            best_util = updated_link_util
            #print("succesfull switch")

    return best_w, best_mlu, best_util


def find_demands_using_max_link(demands, link_util, links, waypoints, timestep, edge_flows):
    # Find link with highest utilization
    max_link_id = max(link_util, key=link_util.get)
    max_util = link_util[max_link_id]
    max_link = links[max_link_id]
    link = (max_link.start, max_link.end)

    # Find all demands that use this link
    demanding_ids = []
    demand_info = []

    for demand_id, demand in enumerate(demands):
        waypoint = waypoints[demand_id][timestep]

        # Check each segment in the waypoint path
        for idx in range(len(waypoint) - 1):
            s1 = waypoint[idx]
            s2 = waypoint[idx + 1]

            # Get edge flow for this segment
            edge_flow = edge_flows.get((s1, s2), {})
            # Check if the max_link is used in this segment
            if link in edge_flow.keys():
                demanding_ids.append(demand_id)
                demand_info.append((
                    demand_id,
                    demand,
                    f"uses link ({max_link.start}, {max_link.end}) in segment ({s1} → {s2})"
                ))
                break  # Only count each demand once

    return max_link, max_util, demanding_ids

def local_search_precomputed_fg(demands, waypoints, edge_flow_all, links, num_nodes,
                                 current_mlu, link_util, timestep, prev_waypoints=None, budget=None):
    curr_link_util = (link_util).copy()

    #Run LS until no improvements found anymore
    improved = True
    while improved:
        improved = False
        for demand_id, demand in enumerate(demands):
            s = demand['s']
            t = demand['t']
            volume = demand['v'][timestep]
            start_w = waypoints[demand_id][timestep]
            current_w = waypoints[demand_id][timestep]
            changing_cost = 0
            candidates = [None] + [n for n in range(num_nodes) if n not in current_w]

            for w in candidates:
                cost = 0
                if len(current_w) == 2: break
                idx = random.choice(range(1, len(current_w)-1))          #Find another waypoint that gets replaced
                temp_w = current_w.copy()
                if w is None:           #if none, remove waypoint
                    temp_w.remove(current_w[idx])
                else:    #else, switch two waypoints
                    temp_w[idx] = w

                #If there is a budget, calculate the cost of changing the waypoints
                if budget is not None and prev_waypoints is not None:
                    # Calculate cost
                    cost = calculate_changing_cost(s, t, current_w, temp_w)
                    if budget - cost < 0: #If it does not fit within the budget, skip
                        continue

                #Compute the mlu for the new waypoint
                new_mlu, updated_link_util = update_mlu_percentages_multiple_waypoints(edge_flow_all, demand, current_w,
                                                                                       temp_w, links, timestep, link_util)

                if new_mlu < current_mlu:
                    current_mlu = new_mlu
                    current_w = temp_w
                    waypoints[demand_id][timestep] = temp_w
                    improved = True
                    curr_link_util = updated_link_util
                    print("improved")
                    if budget:
                        budget = budget + changing_cost - cost
                        changing_cost = cost
                        print("for demand", demand_id, "changed from", start_w, "to", current_w, "costs", changing_cost)
                        print("\t new budget = ", budget)

    return waypoints, curr_link_util, current_mlu


def local_search_precomputed_fg_multiple_moves(graph, demands, waypoints, edge_flow_all, links, num_nodes,
                                current_mlu, link_util, timestep, prev_waypoints=None, budget=None):
    curr_link_util = link_util.copy()

    # Run LS until no improvements found anymore
    improved = True
    iterations = 0
    while improved:
        improved = False
        iterations += 1
        max_link, max_util, demanding_ids = find_demands_using_max_link(
            demands, curr_link_util, links, waypoints, timestep, edge_flow_all
        )

        # --- Phase 1: find the best independent move per demand ---
        # Each move is evaluated against the current (unchanged) link_util,
        # so moves don't interfere with each other during the search phase.
        pending_moves = {}  # demand_id -> updated_w

        adjacent = set(graph[max_link.end].keys())
        adjacent.update(graph[max_link.start].keys())

        for demand_id in demanding_ids:
            demand = demands[demand_id]
            s = demand['s']
            t = demand['t']
            current_w = waypoints[demand_id][timestep]

            candidates = [n for n in adjacent if n not in current_w]
            if len(candidates) <= 1:
                expanded = set()
                for c in candidates:
                    expanded.update(graph[c].keys())
                candidates = [n for n in expanded if n not in current_w]

            p = random.random()
            best_w_for_demand = None
            best_mlu_for_demand = current_mlu  # only accept improvements

            for new_w in candidates:
                if p < 0.33:
                    candidate_w, candidate_mlu, _ = add_waypoint(
                        current_mlu, demand, current_w, new_w, curr_link_util, timestep, edge_flow_all, links)
                elif p < 0.66:
                    candidate_w, candidate_mlu, _ = remove_waypoint(
                        current_mlu, demand, current_w, curr_link_util, timestep, edge_flow_all, links)
                else:
                    candidate_w, candidate_mlu, _ = switch_waypoint(
                        current_mlu, demand, current_w, new_w, curr_link_util, timestep, edge_flow_all, links)

                if candidate_mlu < best_mlu_for_demand:
                    # Check budget if applicable
                    if budget is not None and prev_waypoints is not None:
                        cost = calculate_changing_cost(s, t, current_w, candidate_w)
                        if budget - cost < 0:
                            continue
                    best_mlu_for_demand = candidate_mlu
                    best_w_for_demand = candidate_w

            if best_w_for_demand is not None:
                pending_moves[demand_id] = best_w_for_demand

        if not pending_moves:
            continue  # no improving moves found for any demand this iteration

        # Save old waypoints before touching anything — needed for correct rollback
        old_waypoints = {d: waypoints[d][timestep].copy() for d in pending_moves}

        # --- Phase 2: apply all pending moves simultaneously ---
        for demand_id, updated_w in pending_moves.items():
            waypoints[demand_id][timestep] = updated_w

        # Recompute MLU from scratch over the combined new state
        new_mlu, new_util = compute_mlu_from_percentages(edge_flow_all, demands, links, waypoints, timestep)

        if new_mlu < current_mlu:
            current_mlu = new_mlu
            curr_link_util = new_util
            improved = True
            if budget is not None and prev_waypoints is not None:
                total_cost = sum(
                    calculate_changing_cost(demands[d]['s'], demands[d]['t'], old_waypoints[d], pending_moves[d])
                    for d in pending_moves
                )
                budget -= total_cost
                print(f"  iteration {iterations}: applied {len(pending_moves)} simultaneous moves, "
                      f"new MLU={round(current_mlu, 4)}, budget left={budget}")
            else:
                print(f"  iteration {iterations}: applied {len(pending_moves)} simultaneous moves, "
                      f"new MLU={round(current_mlu, 4)}")
        else:
            # Combined result is not better — roll back all moves using saved old waypoints
            for demand_id in pending_moves:
                waypoints[demand_id][timestep] = old_waypoints[demand_id]

            # Fall back to best single move
            best_single_mlu = current_mlu
            best_single_id = None
            best_single_w = None
            best_single_util = None

            for demand_id, updated_w in pending_moves.items():
                waypoints[demand_id][timestep] = updated_w  # apply just this one
                single_mlu, single_util = compute_mlu_from_percentages(
                    edge_flow_all, demands, links, waypoints, timestep)
                waypoints[demand_id][timestep] = old_waypoints[demand_id]  # restore

                if single_mlu < best_single_mlu:
                    best_single_mlu = single_mlu
                    best_single_id = demand_id
                    best_single_w = updated_w
                    best_single_util = single_util

            # Roll back all moves first
            for demand_id in pending_moves:
                waypoints[demand_id][timestep] = waypoints[demand_id][timestep]  # already old (restored above)

            if best_single_id is not None:
                waypoints[best_single_id][timestep] = best_single_w
                current_mlu = best_single_mlu
                curr_link_util = best_single_util
                improved = True
                print(f"  iteration {iterations}: simultaneous moves conflicted; "
                      f"applied best single move (demand {best_single_id}), "
                      f"new MLU={round(current_mlu, 4)}")

    return waypoints, curr_link_util, current_mlu
