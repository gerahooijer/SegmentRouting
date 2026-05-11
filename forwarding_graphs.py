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
    closed = set()
    dist = [1e7 ] * len(graph)
    dist[source] = 0
    parents = {source: set()}

    while open:
        score, current = heapq.heappop(open)
        closed.add(current)

        #Find all shortest paths
        if current == target:
            continue

        #Add all possible neighbors to open
        for neighbour in graph[current]:
            new_dist = graph[current][neighbour].metric + score
            if new_dist < dist[neighbour]:
                dist[neighbour] = new_dist
                parents[neighbour] = set()
                parents[neighbour].add(current)
            elif new_dist == dist[neighbour]:
                parents[neighbour].add(current)
            if neighbour not in closed:
                heapq.heappush(open, (dist[neighbour], neighbour))
    return dist, parents

def get_all_paths_from_parents(source, target, parents):
    """Reconstruct all shortest paths"""
    all_paths = []
    nodes = set()
    nodes.add(source)

    def dfs(current: int, path: List[int]):
        if current == source:
            all_paths.append([source] + path[::-1])
            return

        for parent in parents.get(current, []):
            dfs(parent, path + [current])
            nodes.add(current)

    if target in parents or target == source:
        dfs(target, [])

    return all_paths, nodes

def ecmp_calculation(source, parents, nodes, volume):
    #Define children
    children = defaultdict(list)
    indegree = defaultdict(int)
    for child, parent_set in parents.items():
        for parent in parent_set:
            if child in nodes:
                children[parent].append(child)
                indegree[child] += 1


    node_flow = defaultdict(float)
    node_flow[source] = volume
    edge_flow = defaultdict(float)

    open = deque([source])

    while open:
        current = open.popleft()
        next_nodes = children[current]
        if not next_nodes:
            continue

        split_flow  = node_flow[current] / len(next_nodes)
        for next in next_nodes:
            node_flow[next] += split_flow
            edge_flow[(current, next)] += split_flow

            indegree[next] -= 1
            if indegree[next] == 0:
                open.append(next)

    return node_flow, edge_flow

def find_forwarding_graph(source, target, graph, links):
    """Find forwarding graph containing all edges on any shortest path"""
    scores, parents = find_shortest_paths(source, target, graph)
    paths, nodes = get_all_paths_from_parents(source, target, parents)

    """Extract the forwarding edges"""
    forwarding_links = []
    for child in parents:
        for parent in parents[child]:
            if child in nodes and parent in nodes:
                link_id = get_link_id(parent,child)
                forwarding_links.append(links[link_id])

    fw_graph = ForwardingGraph(
        source=source,
        target=target,
        links=forwarding_links
    )
    return fw_graph, parents, nodes




