## Problem Statement

Given an adjacency matrix in a 2D array, solve the Single Source Shortest Path algorithm, essentially by implementing the Dijkstra’s algorithm discussed in the previous lesson. We’ve written some skeleton code for the function.

    The value of the weight of the link is graph[src][dst].
    The graph is undirected so graph[src][dst]==graph[dst][src].
    A link between the src and dst exists if -1<graph[src][dst]<16.
    If graph[src][dst]>=16 the weight of the link is infinite and it does not function.

Input

    An adjacency matrix, i.e., a 2D array, a source node, and a destination node.

Output

The shortest path between the source and destination in the form of an array of integers where each integer represents a node and the total weight of the path.

## Example

Input:
```python
graph = [
  [0,1,5,-1,-1],
  [1,0,3,-1,9],
  [5,3,0,4,-1],
  [-1,-1,4,0,2],
  [-1,9,-1,2,0]
]

src = 0
dst = 3
```

Output:

```python
shortest_path = [0,1,2,3]
cost = 8
```
