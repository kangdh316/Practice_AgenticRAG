import networkx as nx

graph = nx.Graph()


def build_graph(entities):

    for i in range(len(entities)-1):

        graph.add_edge(
            entities[i],
            entities[i+1]
        )

    return graph


def expand_entity(entity):

    if entity not in graph:
        return []

    return list(
        graph.neighbors(entity)
    )