## HTTP0.9 playground

出典: 『Real World HTTP 第3版 ―歴史とコードに学ぶインターネットとウェブ技術』（渋川よしき）

## Handson

In HTTP0.9, the client just send a GET request to get contents, and server serves html body. That's it!

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
