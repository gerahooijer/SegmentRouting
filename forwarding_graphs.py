import heapq
from dataclasses import dataclass
from typing import List, Tuple, Dict
from read_input import _link_map, get_link_id
from collections import defaultdict, deque

@dataclass
class ForwardingGraph:
    source: int
    target: int
    links: List[Tuple[int, float]]

def find_shortest_paths(source, target, graph):
    start = (0, source)
    open = [start]
    closed = []
    all_scores = {source: 0}
    parents = {source: []}

    while open:
        score, current = heapq.heappop(open)
        closed.append(current)

        #Find all shortest paths
        if current == target:
            continue

        #Add all possible neighbours to open
        for neighbour in graph[current]:
            tentative_score = graph[current][neighbour].metric + score

            if neighbour not in all_scores:
                all_scores[neighbour] = 1e7

            if tentative_score < all_scores[neighbour]:
                all_scores[neighbour] = tentative_score
                heapq.heappush(open, (tentative_score, neighbour))
                parents[neighbour] = [current]
            elif tentative_score == all_scores[neighbour]:
                parents[neighbour].append(current)
    return all_scores, parents

"""def get_all_paths_from_parents(source, target, parents):
    all_paths = []

    def dfs(current: int, path: List[int]):
        if current == source:
            all_paths.append([source] + path[::-1])
            return

        for parent in parents.get(current, []):
            dfs(parent, path + [current])

    if target in parents or target == source:
        dfs(target, [])

    return all_paths"""

def get_all_paths_from_parents(source, target, parents):
    """Reconstruct all shortest paths"""
    all_paths = []

    def dfs(current: int, path: List[int]):
        if current == source:
            all_paths.append([source] + path[::-1])
            return

        for parent in parents.get(current, []):
            dfs(parent, path + [current])

    if target in parents or target == source:
        dfs(target, [])

    return all_paths

def ecmp_calculation(source, target, parents, fw_graph, volume, links):
    current = source

    node_flow = defaultdict(float)
    edge_flow = defaultdict(float)

    node_flow[source] = volume
    open = deque([source])
    visited = set()
    link_load = [0 for _ in range(len(links))]

    while open:
        current = open.popleft()
        if current in visited:
            continue
        visited.add(current)
        print("we visit node", current)

        outgoing = 0
        next = []
        for links in fw_graph.links:
            if links.start == current:
                outgoing += 1
                next.append(links.end)
        for node in next:
            link_id = get_link_id(current, node)
            node_flow[node] += node_flow[current] / len(next)
            link_load[link_id] += node_flow[node]
            print("next is", node)
            print("new node flow is:", node_flow[node])
            print("new link load is:", link_load[link_id], "\n")
            open.append(node)
    print(link_load)
    print("flow on every node:", node_flow)




    for parent in parents[current]:
        num_parents = len(parents[current])
        link_id = get_link_id(parent, current)
        link_load[link_id] = 1 / num_parents

    print(link_load)
    return None

def find_forwarding_graph(source, target, graph, links):
    """Find forwarding graph containing all edges on any shortest path"""
    scores, parents = find_shortest_paths(source, target, graph)
    paths = get_all_paths_from_parents(source, target, parents)

    # Build set of all edges that are on shortest paths
    forwarding_edges = set()

    # Iterate through parents dictionary to extract edges
    for child, parent_list in parents.items():
        for parent in parent_list:
            for path in paths:
                if child in path and parent in path:
                    # Add link_id from parent to child
                    link_id= get_link_id(parent, child)
                    forwarding_edges.add(link_id)
                    continue

    #Add the actual links
    forwarding_links = []
    for link_id in forwarding_edges:
        link = links[link_id]
        forwarding_links.append(link)

    fw_graph = ForwardingGraph(
        source=source,
        target=target,
        links=forwarding_links
    )
    return fw_graph, parents

"""
def find_forwarding_graph(source, target, graph, links):
    scores, parents = find_shortest_paths(source, target, graph)
    paths = get_all_paths_from_parents(source, target, parents)
    return paths"""




