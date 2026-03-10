## What's Proxy in HTTP?

A proxy server makes requests on behalf of a client (or receives requests on behalf of a server, in reverse proxy setups).

With proxy:

Client → Proxy → Server

Without proxy:

Client → Server

## Why proxy is used?

1. caching
2. security
3. network gateway/control
4. load balancing (reverse proxy)

### Cache

In earlier internet environments, bandwidth was limited. Caching responses at a proxy reduced traffic between clients and origin servers.

### Security

A proxy can inspect, filter, and control requests before they reach the origin server. This can reduce direct exposure of internal servers.

### Network

A proxy can act as a network gateway for outbound or inbound traffic control.

### Load Balancing (Reverse Proxy)

Client → Reverse Proxy → App Server

Example:

```
Cloudflare
NGINX
Envoy
HAProxy
```

Use cases (not only load balancing)
```
TLS termination
load balancing
WAF
caching
routing
```

## Difference: Forward proxy vs Reverse proxy

Originally, "proxy" often referred to a client-side proxy (forward proxy), which acts on behalf of clients.
A reverse proxy applies the same idea on the server side: it acts on behalf of servers.

Forward proxy:

```
社員PC → 社内proxy → Internet
```

The proxy makes requests to the internet on behalf of clients.

```
[Client] → [Proxy] → Internet → [Server]
```

So, a forward proxy manages client-side outbound requests.

Reverse proxy:

```
Client → Reverse Proxy → Server

e.g.
browser → Cloudflare → origin server
```

Overall flow:

```
[Client] → Internet → [Reverse Proxy] → [Server]
```

## Difference between Proxy and Gateway

It is hard to draw a perfectly strict boundary, but this is a practical distinction:

- A gateway is a broader concept: an entry point between networks/systems, often with policy enforcement and sometimes protocol translation.
- A proxy mainly relays requests/responses on behalf of another endpoint.

In practice, when handling external traffic at a system boundary, people often call it a gateway.
When relaying requests inside or between services, people often call it a proxy.
