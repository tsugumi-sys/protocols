## HTTP0.9 playground

出典: 『Real World HTTP 第3版 ―歴史とコードに学ぶインターネットとウェブ技術』（渋川よしき）

## Hands-on

In HTTP/0.9, the client just sends a GET request to fetch content, and the server returns an HTML body. That's it.

Note: The following results use HTTP/1.0 because HTTP/0.9 compatibility is currently broken.

Client logs.

```sh
curl --http1.0 http://localhost:18888/greeting
# <html><body>hello</body></html>
```

Server logs.

```sh
2026/03/07 14:56:04 start http listening :18888
GET /greeting HTTP/1.0
Host: localhost:18888
Accept: */*
User-Agent: curl/8.13.0
```

## From HTTP/0.9 to HTTP/1.0

Client side:

- When a user makes a request, they specify the method (GET) and HTTP version.
- New fields were added, such as `Host`, `User-Agent`, and `Accept`.
- Users can send data in the request body.

Server side:

- Status codes (200, etc.) were added.

## What is a MIME type?

A MIME type is a string used to distinguish file types. It originally comes from email.
