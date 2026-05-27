from collections import defaultdict

def remove_downed_links(graph, interventions, timestep):
    downed_link_ids = set()
    for intervention in interventions:
        if intervention['t'] == timestep:
            for link_id in intervention['links']:
                downed_link_ids.add(link_id)
    new_graph = defaultdict(dict)
    for u in graph:
        for v in graph[u]:
            link = graph[u][v]
            if link.id not in downed_link_ids:
                new_graph[u][v] = link
    return new_graph