import json
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, Tuple, Optional

@dataclass
class Link:
    id: int
    start: int
    end: int
    metric: int
    capacity: int

_link_map: Dict[Tuple[int, int], Link] = {}

def get_link(start: int, end: int) -> Optional[Link]:
    return _link_map.get((start, end))

def get_link_id(start: int, end: int) -> Optional[int]:
    link = get_link(start, end)
    return link.id if link else None

def read_input(instance):
    with open(f'setA/setA-{instance}-net.json', 'r') as file:
        data = json.load(file)

    directed = data['directed']
    multigraph = data['multigraph']
    nodes = data['nodes']
    links = data['links']
    graph = (directed, multigraph, nodes, links)

    with open(f'setA/setA-{instance}-scenario.json', 'r') as file:
        data = json.load(file)

    max_segments = data['max_segments']
    budget = data['budget']
    interventions = data['interventions']

    scenario = (max_segments, budget, interventions)

    with open(f'setA/setA-{instance}-tm.json', 'r') as file:
        data = json.load(file)

    num_time_slots = data['num_time_slots']
    demands = data['demands']

    tm = (num_time_slots, demands)

    return graph, scenario, tm

def generate_adjacency_lists(input):
    global _link_map
    directed, multigraph, nodes, links = input

    """
    Graph data structure:
    {node: {neighbour: link, neighbour: link, ...}, node: {neighbour: link, neighbour: link,...},...}
    """
    graph = defaultdict(dict)
    links_list = []
    for link in links:
        link = Link(link["id"], link["from"], link["to"], link["metric"], link["capacity"])
        start = link.start
        end = link.end
        graph[start][end]=link
        links_list.append(link)
    _link_map = {(link.start, link.end): link for link in links_list}

    return graph, links_list
