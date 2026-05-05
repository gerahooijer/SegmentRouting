from read_input import read_input, generate_adjacency_lists, Link, get_link_id
from forwarding_graphs import find_forwarding_graph, ecmp_calculation
from generate_output_file import output_file

if __name__ == '__main__':
    #Read in the instance, and generate the adjacency list
    instance = '21'
    input_graph, scenario, traffic_matrix = read_input(instance)
    graph, links = generate_adjacency_lists(input_graph)

    #Calculate the forwarding graphs for every demand node pair
    num_time_slots, demands = traffic_matrix
    link_load =[[0 for _ in enumerate(links)]for _ in range(num_time_slots)]
    links_used = [[]for _ in range(num_time_slots)]
    time_that_link_is_used = [[0 for _ in enumerate(links)] for _ in range(num_time_slots)]

    for demand in demands:
        source = demand['s']
        target = demand['t']
        fw_graph, parents = find_forwarding_graph(source, target, graph, links)

        for time in range(num_time_slots):
            volume = demand['v'][time]
            ecmp_calculation(source, target, parents, fw_graph, volume, links)

        #print(fw_graph)

        outgoing = [0 for _ in range(len(graph))]
        ingoing = [0 for _ in range(len(graph))]

        for link in fw_graph.links:
            outgoing[link.start] +=1
            ingoing[link.end] += 1
        #print(outgoing)
        for time in range(num_time_slots):
            volume = demand['v'][time]
            for link in fw_graph.links:
                link_load[time][link.id] = volume / outgoing[link.start]

        #print(link_load[time])
    """for demand in demands:
        source = demand['s']
        target = demand['t']

        paths = find_forwarding_graph(source, target, graph, links)
        print( "for demand from ", source, "to ", target, "the routes are ", paths)

        "Calculate the link load for each time slot"
        for time in range(num_time_slots):
            volume = demand['v'][time]
            for path in paths:
                for id in range(len(path) - 1):
                    start = path[id]
                    end = path[id+1]
                    link_id = get_link_id(start, end)

                    if link_id not in links_used[time]:
                        links_used[time].append(link_id)
                    time_that_link_is_used[time][link_id] += 1
                    #link_load[time][link_id] =+ volume /len(paths)
            max_usage = sorted(time_that_link_is_used[time], reverse = True)[0]
            for link_id in range(len(links)):
                link_load[time][link_id] = time_that_link_is_used[time][link_id] / max_usage * volume
    for time in range(num_time_slots):
        print(link_load[time])

    for time in range(num_time_slots):
        #print("the links used in timeslot", time, "are \n", sorted(links_used[time]))
        utilizations = [round(link_load[time][link], 2) for link in range(len(links))]
        print("with utilization", utilizations, "\n")

    "Find the links with the highest loads"
    max_loads = []
    max_links = []
    for time in range(num_time_slots):
        max_load = 0
        max_link = None
        for link in range(len(links)):
            if link_load[time][link] > max_load:
                max_load = link_load[time][link]
                max_link = link
        max_loads.append(max_load)
        max_links.append(max_link)

        print("For timeslot ", time, "the maximum load is ", round(max_load, 2), "on link", max_link)

    output_file(demands, num_time_slots, instance)"""