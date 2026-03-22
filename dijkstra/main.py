def Dijkstra(graph, src, dst):
    n = len(graph)
    inf = float("inf")

    if src == dst:
        return [src], 0

    dist = [inf] * n
    parent = [None] * n
    visited = set()

    dist[src] = 0

    while len(visited) < n:
        current = None
        current_cost = inf

        # Pick the unvisited node with the smallest tentative distance.
        for node in range(n):
            if node not in visited and dist[node] < current_cost:
                current = node
                current_cost = dist[node]

        if current is None:
            break

        if current == dst:
            break

        visited.add(current)

        for neighbor in range(n):
            weight = graph[current][neighbor]

            if weight == -1 or weight >= 16:
                continue

            if neighbor in visited:
                continue

            new_cost = dist[current] + weight
            if new_cost < dist[neighbor]:
                dist[neighbor] = new_cost
                parent[neighbor] = current

    if dist[dst] == inf:
        return [], inf

    path = []
    node = dst
    while node is not None:
        path.append(node)
        node = parent[node]

    path.reverse()
    return path, dist[dst]
