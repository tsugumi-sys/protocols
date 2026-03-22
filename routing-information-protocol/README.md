# Routing Information Protocol

小さな RIP シミュレーションです。各ルーターは自分の routing table を隣接ルーターへ広告し、受信側はリンクコストを足して自分の table を更新します。

## What This Code Models

- `Router`: RIP ルーター本体。routing table と port を持ちます。
- `RipEntry`: routing table の 1 行です。
- `RipPacket`: 隣接ルーターへ送る経路広告です。
- `Port` / `PortLink`: どのポートがどのルーターへ何コストでつながっているかを表します。
- `topology_to_routers()`: 簡単なトポロジ記述からルーター群を構築します。

## RIP Algorithm in This Repository

1. 各ルーターは自分自身への経路を `cost=0` で持ちます。
2. `send_rip_packets()` が隣接ルーターへ現在の routing table を送ります。
3. `receive_rip_packets()` は `neighbor_link_cost + advertised_cost` を計算します。
4. 未知の宛先なら新規追加し、同じ next hop の更新またはより安い経路なら上書きします。

これは簡易版のため、split horizon や poison reverse のような実運用向け最適化は入れていません。

## Topology Format

トポロジは次の形式で書きます。

```python
[
    (
        "<router-ip>",
        ("<local-port-ip>", "<neighbor-router-ip>", "<neighbor-port-ip>", <cost>),
        ...
    ),
    ...
]
```

例:

```python
topology = [
    ("10.0.0.1", ("192.168.1.1", "10.0.0.2", "192.168.1.2", 1)),
    (
        "10.0.0.2",
        ("192.168.1.2", "10.0.0.1", "192.168.1.1", 1),
        ("192.168.2.1", "10.0.0.3", "192.168.2.2", 1),
    ),
    ("10.0.0.3", ("192.168.2.2", "10.0.0.2", "192.168.2.1", 1)),
]
```

## Example

```python
from topology_reader import topology_to_routers

routers = topology_to_routers(topology)
for router in routers:
    router.send_rip_packets(routers)

router_c = next(router for router in routers if router.ip_address == "10.0.0.3")
entry_to_a = router_c.find_rip_entry("10.0.0.1")

print(entry_to_a.cost)         # 2
print(entry_to_a.next_hop_ip)  # 10.0.0.2
```

## Running the Demo

```bash
python3 main.py
```

## Running the Tests

`pytest` を使います。

```bash
pytest
```

もしローカルに `pytest` がまだなければ、依存追加後にインストールしてください。
