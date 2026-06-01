import heapq
from collections import defaultdict, deque

def find_shortest_paths(source, graph):
    start = (0, source)
    open = [start]
    dist = [1e7 ] * len(graph)
    dist[source] = 0
    parents = {source: set()}

    while open:
        score, current = heapq.heappop(open)

        if score > dist[current]:
            continue

        #Add all possible neighbors to open
        for neighbour in graph[current]:
            new_dist = graph[current][neighbour].metric + score
            if new_dist < dist[neighbour]:
                dist[neighbour] = new_dist
                parents[neighbour] = set()
                parents[neighbour].add(current)
                heapq.heappush(open, (dist[neighbour], neighbour))
            elif new_dist == dist[neighbour]:
                parents[neighbour].add(current)

    return dist, parents

def ecmp_calculation(source, parents, nodes, volume):

    node_flow = defaultdict(float)
    node_flow[source] = volume
    edge_flow = defaultdict(float)

    open = deque([source])
    indegree = defaultdict(int)
    children = defaultdict(list)
    for child, parent_set in parents.items():
        for parent in parent_set:
            if child in nodes:
                children[parent].append(child)
                indegree[child] += 1

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

def get_all_forwarding_graphs(graph, links, num_nodes):
    edge_flows = {}

    for s in range(num_nodes ):
        scores, parents = find_shortest_paths(s, graph)

        for t in range(num_nodes):
            if s == t:
                continue

            nodes_in_fg = set()
            stack = [t]
            while stack:
                u = stack.pop()
                if u in nodes_in_fg:
                    continue
                nodes_in_fg.add(u)
                for p in parents.get(u, []):
                    stack.append(p)

            node_flow, edge_flow = ecmp_calculation(s, parents, nodes_in_fg, volume = 1)
            edge_flows[(s, t)] = dict(edge_flow)

    return edge_flows
