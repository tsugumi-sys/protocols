from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import Dijkstra


@pytest.mark.parametrize(
    ("graph", "src", "dst", "expected_path", "expected_cost"),
    [
        (
            [
                [0, 1, 5, -1, -1],
                [1, 0, 3, -1, 9],
                [5, 3, 0, 4, -1],
                [-1, -1, 4, 0, 2],
                [-1, 9, -1, 2, 0],
            ],
            0,
            3,
            [0, 1, 2, 3],
            8,
        ),
        (
            [
                [0, 7, 9, -1, -1, 14],
                [7, 0, 10, 15, -1, -1],
                [9, 10, 0, 11, -1, 2],
                [-1, 15, 11, 0, 6, -1],
                [-1, -1, -1, 6, 0, 9],
                [14, -1, 2, -1, 9, 0],
            ],
            0,
            4,
            [0, 2, 5, 4],
            20,
        ),
        (
            [
                [0, 2, 16, 10],
                [2, 0, 3, -1],
                [16, 3, 0, 1],
                [10, -1, 1, 0],
            ],
            0,
            3,
            [0, 1, 2, 3],
            6,
        ),
        (
            [
                [0, 4, 1, -1],
                [4, 0, 2, 1],
                [1, 2, 0, 5],
                [-1, 1, 5, 0],
            ],
            2,
            3,
            [2, 1, 3],
            3,
        ),
    ],
)
def test_dijkstra_returns_shortest_path_and_cost(
    graph, src, dst, expected_path, expected_cost
):
    path, cost = Dijkstra(graph, src, dst)

    assert path == expected_path
    assert cost == expected_cost


def test_dijkstra_returns_zero_cost_when_src_equals_dst():
    graph = [
        [0, 5, -1],
        [5, 0, 2],
        [-1, 2, 0],
    ]

    path, cost = Dijkstra(graph, 1, 1)

    assert path == [1]
    assert cost == 0
