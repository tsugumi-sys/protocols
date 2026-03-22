## Mini gRPC

Let's create an TCP based protocl works like gRPC.

Clients send a message like 

```json
{
  "version": 1,
  "request_id": "abc-123",
  "method": "add",
  "params": {
    "a": 10,
    "b": 20
  }
}
```

Servers respond with a message like

```json
{
  "request_id": "abc-123",
  "ok": true,
  "result": 30,
  "error": null
}
```

## Design

### Transport layer Protocol

Let's use TCP. In gRPC, we should prefer messaging reliability.
We may use UDP but we need to handle reliability stuff on the application layer.

### Selialization

Let's use JSON. The actual gRPC uses protobuf for smaller message size.

### Framing

TCP does not have message boundary. Event a client send messages with 2 times send, the sever receives with 1 recv.

Let's use length-prefixed boundary.

```
[4-byte length][json bytes]
```

The receiver first reads length, then we read bytes of its length.
