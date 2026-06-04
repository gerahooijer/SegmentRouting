import random
from collections import defaultdict
from read_input import get_link_id
from copy import deepcopy
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

    seg_old = set(segment_path(old_w))
    seg_new = set(segment_path(new_w))

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


def segment_path(waypoint):
    segment = []
    for idx in range(len(waypoint)-1):
        segment.append((waypoint[idx], waypoint[idx+1]))
    return segment

def calculate_changing_cost (old_w, new_w):
    seg_1 = set(segment_path(old_w))
    seg_2 = set(segment_path(new_w))
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


def perturbation(waypoints, demands, edge_flow_all, links, timestep, graph, num_nodes,
                 perturbation_strength, current_mlu=None, curr_link_util=None):

    perturbed_waypoints = deepcopy(waypoints)
    #print("perturbation strength", perturbation_strength)
    # Select random demands to perturb
    num_demands = len(demands)
    num_to_perturb = min(perturbation_strength, num_demands)
    demands_to_perturb = random.sample(range(num_demands), num_to_perturb)

    for demand_id in demands_to_perturb:
        demand = demands[demand_id]
        current_w = perturbed_waypoints[demand_id][timestep]

        # Randomly choose perturbation type
        p = random.random()

        if p < 0.33 and len(current_w) > 2:
            # Remove a random waypoint (except source and destination)
            if len(current_w) > 2:
                idx_to_remove = random.randint(1, len(current_w) - 2)
                current_w = current_w[:idx_to_remove] + current_w[idx_to_remove + 1:]

        elif p < 0.66:
            # Add a random waypoint at a random position
            available = [n for n in range(num_nodes) if n not in current_w]
            if available:
                new_waypoint = random.choice(available)
                insert_pos = random.randint(1, len(current_w) - 1)
                current_w = current_w[:insert_pos] + [new_waypoint] + current_w[insert_pos:]

        else:
            # Switch a random waypoint with a random node
            if len(current_w) > 2:
                idx_to_switch = random.randint(1, len(current_w) - 2)
                available = [n for n in range(num_nodes) if n not in current_w]
                if available:
                    new_node = random.choice(available)
                    current_w[idx_to_switch] = new_node

        perturbed_waypoints[demand_id][timestep] = current_w

    # Compute MLU for perturbed solution
    perturbed_mlu, perturbed_link_util = compute_mlu_from_percentages(
        edge_flow_all, demands, links, perturbed_waypoints, timestep
    )


    return perturbed_waypoints, perturbed_mlu, perturbed_link_util


def local_search_with_perturbation(graph, demands, waypoints, edge_flow_all, links, num_nodes,
                                   current_mlu, link_util, timestep, prev_waypoints=None, budget=None,
                                   max_no_improve_iterations=100, perturbation_strength=10, max_time = 30):

    curr_link_util = link_util.copy()
    og_waypoints = deepcopy(waypoints)
    og_mlu = current_mlu
    improved = True
    iterations = 0
    no_improve_count = 0
    best_mlu = current_mlu
    best_waypoints = deepcopy(waypoints)
    best_link_util = curr_link_util.copy()
    best_budget = budget
    start_time = time.time()
    total_budget = budget
    current_budget = budget
    og_link_util = curr_link_util.copy()
    improved_time = time.time()

    while improved or no_improve_count < max_no_improve_iterations:
        if time.time() - start_time > max_time:
            #print("time spent in LS", (time.time() - start_time) )
            break
        improved = False
        iterations += 1

        # Try to find improving moves
        max_link, max_util, demanding_ids = find_demands_using_max_link(
            demands, curr_link_util, links, waypoints, timestep, edge_flow_all
        )

        pending_moves = {}
        adjacent = set(graph[max_link.end].keys())
        adjacent.update(graph[max_link.start].keys())

        for demand_id in demanding_ids:
            demand = demands[demand_id]
            current_w = waypoints[demand_id][timestep]

            candidates = [n for n in adjacent if n not in current_w]
            if len(candidates) <= 1:
                expanded = set()
                for c in candidates:
                    expanded.update(graph[c].keys())
                candidates = [n for n in expanded if n not in current_w]

            p = random.random()
            best_w_for_demand = None
            best_mlu_for_demand = current_mlu

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
                    if budget is not None and prev_waypoints is not None:
                        cost = 0
                        cost -= calculate_changing_cost(og_waypoints[demand_id][timestep], current_w)
                        cost += calculate_changing_cost(og_waypoints[demand_id][timestep], candidate_w)
                        if current_budget - cost < 0:
                            continue
                    best_mlu_for_demand = candidate_mlu
                    best_w_for_demand = candidate_w

            if best_w_for_demand is not None:
                pending_moves[demand_id] = best_w_for_demand

        old_waypoints = {d: waypoints[d][timestep].copy() for d in pending_moves}

        for demand_id, updated_w in pending_moves.items():
            waypoints[demand_id][timestep] = updated_w

        new_mlu, new_util = compute_mlu_from_percentages(edge_flow_all, demands, links, waypoints, timestep)

        if new_mlu < current_mlu:
            if budget is not None and prev_waypoints is not None:
                total_cost = 0
                for d in pending_moves:
                    total_cost -= calculate_changing_cost(og_waypoints[d][timestep], old_waypoints[d])
                    total_cost += calculate_changing_cost(og_waypoints[d][timestep], pending_moves[d])

                if current_budget - total_cost < 0:
                    for demand_id in pending_moves:
                        waypoints[demand_id][timestep] = old_waypoints[demand_id]
                    continue
                current_budget -= total_cost

            current_mlu = new_mlu
            curr_link_util = new_util
            improved = True
            no_improve_count = 0

            # Track best solution found
            if current_mlu < best_mlu:
                best_mlu = current_mlu
                best_budget = current_budget
                best_waypoints = deepcopy(waypoints)
                best_link_util = curr_link_util.copy()
                improved = True
                improved_time = time.time()
                #print("new best", best_mlu, "after", round((time.time()-start_time), 2))
                #print("budget", best_budget)

        else:
            for demand_id in pending_moves:
                waypoints[demand_id][timestep] = old_waypoints[demand_id]

            best_single_mlu = current_mlu
            best_single_id = None
            best_single_w = None
            best_single_util = None

            for demand_id, updated_w in pending_moves.items():
                single_mlu, single_util = update_mlu_percentages_multiple_waypoints(
                    edge_flow_all, demands[demand_id], waypoints[demand_id][timestep],
                    updated_w, links, timestep, curr_link_util
                )

                if single_mlu < best_single_mlu:
                    best_single_mlu = single_mlu
                    best_single_id = demand_id
                    best_single_w = updated_w
                    best_single_util = single_util

            if best_single_id is not None:
                if budget is not None and prev_waypoints is not None:
                    cost = -calculate_changing_cost(og_waypoints[best_single_id][timestep],
                                                    waypoints[best_single_id][timestep])
                    cost += calculate_changing_cost(og_waypoints[best_single_id][timestep], best_single_w)
                    if current_budget - cost < 0:
                        no_improve_count += 1
                        continue
                    current_budget -= cost

                waypoints[best_single_id][timestep] = best_single_w
                current_mlu = best_single_mlu
                curr_link_util = best_single_util
                improved = True
                no_improve_count = 0

                # Track best solution found
                if current_mlu < best_mlu:
                    best_mlu = current_mlu
                    best_budget = current_budget
                    best_waypoints = deepcopy(waypoints)
                    best_link_util = curr_link_util.copy()
                    improved = True
                    improved_time = time.time()
                    #print("new best", best_mlu, "after", round((time.time() - start_time), 2))

                    #print("new best", best_mlu)
                    #print("best budget", best_budget)
            else:
                no_improve_count += 1
                if no_improve_count >= max_no_improve_iterations:
                    # print(f"No improvement for {no_improve_count} iterations. Applying perturbation...")
                    # Apply perturbation
                    updated_waypoints, updated_mlu, updated_link_util = perturbation(
                        og_waypoints, demands, edge_flow_all, links, timestep, graph, num_nodes,
                        perturbation_strength=perturbation_strength,
                        current_mlu=og_mlu, curr_link_util=og_link_util)
                    #print("perturbation")
                    if total_budget != None:
                        cost = 0
                        for demand_id, demand in enumerate(demands):
                            if updated_waypoints[demand_id][0] != updated_waypoints[demand_id][1]:
                                cost += calculate_changing_cost(og_waypoints[demand_id][0],
                                                                updated_waypoints[demand_id][1])
                                # print("for demand", demand_id, "cost", cost, "wp", updated_waypoints[demand_id])
                        if total_budget - cost < 0:
                            # print("perturbation not within budget")
                            # print("total budget is")
                            continue
                        current_budget = total_budget - cost
                    waypoints = updated_waypoints
                    current_mlu = updated_mlu
                    curr_link_util = updated_link_util
                    no_improve_count = 0
                continue

    total = 0
    if timestep == 1:
        # print("\n \n final costs")
        for demand_id, demands in enumerate(demands):
            if waypoints[demand_id][0] != waypoints[demand_id][1]:
                total += calculate_changing_cost(waypoints[demand_id][0], waypoints[demand_id][1])
                # print("demand", demand_id, "from ", waypoints[demand_id], "cost:", calculate_changing_cost(waypoints[demand_id][0], waypoints[demand_id][1]))
        #print("total cost", total)

    #print(iterations)
    return best_waypoints, best_link_util, best_mlu, best_budget

def local_search_with_perturbation2(graph, demands, waypoints, edge_flow_all, links, num_nodes,
                                   current_mlu, link_util, timestep, prev_waypoints=None, budget=None,
                                   max_no_improve_iterations=100, perturbation_strength=10):
    curr_link_util = link_util.copy()
    og_waypoints = deepcopy(waypoints)
    og_mlu = current_mlu
    improved = True
    iterations = 0
    no_improve_count = 0
    best_mlu = current_mlu
    best_waypoints = deepcopy(waypoints)
    best_link_util = curr_link_util.copy()
    best_budget = budget
    start_time = time.time()
    total_budget = budget
    current_budget = budget
    og_link_util = curr_link_util.copy()
    improved_time = time.time()

    while improved or no_improve_count < max_no_improve_iterations:
        if time.time() - start_time > 30:
            #print("time spent in LS", (time.time() - start_time) )
            break
        improved = False
        iterations += 1

        # Try to find improving moves
        max_link, max_util, demanding_ids = find_demands_using_max_link(
            demands, curr_link_util, links, waypoints, timestep, edge_flow_all
        )

        pending_moves = {}
        adjacent = set(graph[max_link.end].keys())
        adjacent.update(graph[max_link.start].keys())

        for demand_id in demanding_ids:
            demand = demands[demand_id]
            current_w = waypoints[demand_id][timestep]

            candidates = [n for n in adjacent if n not in current_w]
            if len(candidates) <= 1:
                expanded = set()
                for c in candidates:
                    expanded.update(graph[c].keys())
                candidates = [n for n in expanded if n not in current_w]

            p = random.random()
            best_w_for_demand = None
            best_mlu_for_demand = current_mlu

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
                    if budget is not None and prev_waypoints is not None:
                        cost = 0
                        cost -= calculate_changing_cost(og_waypoints[demand_id][timestep], current_w)
                        cost += calculate_changing_cost(og_waypoints[demand_id][timestep], candidate_w)
                        if current_budget - cost < 0:
                            continue
                    best_mlu_for_demand = candidate_mlu
                    best_w_for_demand = candidate_w

            if best_w_for_demand is not None:
                pending_moves[demand_id] = best_w_for_demand

        old_waypoints = {d: waypoints[d][timestep].copy() for d in pending_moves}

        for demand_id, updated_w in pending_moves.items():
            waypoints[demand_id][timestep] = updated_w

        new_mlu, new_util = compute_mlu_from_percentages(edge_flow_all, demands, links, waypoints, timestep)

        if new_mlu < current_mlu:
            if budget is not None and prev_waypoints is not None:
                total_cost = 0
                for d in pending_moves:
                    total_cost -= calculate_changing_cost(og_waypoints[d][timestep], old_waypoints[d])
                    total_cost += calculate_changing_cost(og_waypoints[d][timestep], pending_moves[d])

                if current_budget - total_cost < 0:
                    for demand_id in pending_moves:
                        waypoints[demand_id][timestep] = old_waypoints[demand_id]
                    continue
                current_budget -= total_cost

            current_mlu = new_mlu
            curr_link_util = new_util
            improved = True
            no_improve_count = 0

            # Track best solution found
            if current_mlu < best_mlu:
                best_mlu = current_mlu
                best_budget = current_budget
                best_waypoints = deepcopy(waypoints)
                best_link_util = curr_link_util.copy()
                improved = True
                improved_time = time.time()
                #print("new best", best_mlu, "found after", (round((time.time() - start_time), 2)))
                #print("budget", best_budget)

        else:
            for demand_id in pending_moves:
                waypoints[demand_id][timestep] = old_waypoints[demand_id]

            best_single_mlu = current_mlu
            best_single_id = None
            best_single_w = None
            best_single_util = None

            for demand_id, updated_w in pending_moves.items():
                single_mlu, single_util = update_mlu_percentages_multiple_waypoints(
                    edge_flow_all, demands[demand_id], waypoints[demand_id][timestep],
                    updated_w, links, timestep, curr_link_util
                )

                if single_mlu < best_single_mlu:
                    best_single_mlu = single_mlu
                    best_single_id = demand_id
                    best_single_w = updated_w
                    best_single_util = single_util

            if best_single_id is not None:
                if budget is not None and prev_waypoints is not None:
                    cost = -calculate_changing_cost(og_waypoints[best_single_id][timestep],
                                                    waypoints[best_single_id][timestep])
                    cost += calculate_changing_cost(og_waypoints[best_single_id][timestep], best_single_w)
                    if current_budget - cost < 0:
                        no_improve_count += 1
                        continue
                    current_budget -= cost

                waypoints[best_single_id][timestep] = best_single_w
                current_mlu = best_single_mlu
                curr_link_util = best_single_util
                improved = True
                no_improve_count = 0

                # Track best solution found
                if current_mlu < best_mlu:
                    best_mlu = current_mlu
                    best_budget = current_budget
                    best_waypoints = deepcopy(waypoints)
                    best_link_util = curr_link_util.copy()
                    improved = True
                    improved_time = time.time()

                    #print("new best", best_mlu, "found after", (round((time.time() - start_time), 2)))
                    #print("new best", best_mlu)
                    #print("best budget", best_budget)
            else:
                no_improve_count += 1
                if no_improve_count >= max_no_improve_iterations:
                    # print(f"No improvement for {no_improve_count} iterations. Applying perturbation...")
                    # Apply perturbation
                    # print("perturbation strength", perturbation_strength)
                    updated_waypoints, updated_mlu, updated_link_util = perturbation(
                        og_waypoints, demands, edge_flow_all, links, timestep, graph, num_nodes,
                        perturbation_strength=perturbation_strength,
                        current_mlu=og_mlu, curr_link_util=og_link_util)
                    #print("perturb after", round((time.time() - start_time), 2), "seconds")
                    if total_budget != None:
                        cost = 0
                        for demand_id, demand in enumerate(demands):
                            if updated_waypoints[demand_id][0] != updated_waypoints[demand_id][1]:
                                cost += calculate_changing_cost(og_waypoints[demand_id][0],
                                                                updated_waypoints[demand_id][1])
                                #print("for demand", demand_id, "cost", cost, "wp", updated_waypoints[demand_id])
                        if total_budget - cost < 0:
                            #print("perturbation not within budget")
                            #print("total budget is")
                            continue
                        current_budget = total_budget - cost
                    waypoints = updated_waypoints
                    current_mlu = updated_mlu
                    curr_link_util = updated_link_util
                    no_improve_count = 0
                continue

    total = 0
    if timestep == 1:
        # print("\n \n final costs")
        for demand_id, demands in enumerate(demands):
            if waypoints[demand_id][0] != waypoints[demand_id][1]:
                total += calculate_changing_cost(waypoints[demand_id][0], waypoints[demand_id][1])
                # print("demand", demand_id, "from ", waypoints[demand_id], "cost:", calculate_changing_cost(waypoints[demand_id][0], waypoints[demand_id][1]))
        #print("total cost", total)

    #print(iterations)
    return best_waypoints, best_link_util, best_mlu, best_budget
