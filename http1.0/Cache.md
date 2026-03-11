## How does ETag work?

When a server sends a response to a browser like this:

```
HTTP/1.1 200 OK
ETag: "abc123"
Content-Type: text/css
```

The browser saves the `ETag` value.

The next time, the browser sends a request with an `If-None-Match` header like this:

```
GET /style.css
If-None-Match: "abc123"
```

Then the server checks the current `ETag`.

If it is the same:
```
HTTP/1.1 304 Not Modified
```

The content is not sent. The browser uses the cached content.

If it is different:
```
HTTP/1.1 200 OK
ETag: "xyz999"
```

New content is sent.

## How does the Cache-Control header field work?

### How are Cache-Control and ETag different?

`Cache-Control`: Manages the cache TTL.
`ETag`: Checks whether the content is still the latest version.

### How does Cache-Control work?

`Cache-Control` defines whether the response can be cached and, if it can, how long it may be cached.


Flow:

```
Cache-Control
     ↓
Cache TTL expired.
     ↓
Check with ETag
```
