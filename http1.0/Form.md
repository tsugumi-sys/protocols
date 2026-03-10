## What is form?

A form is a mechanism for sending user input from a browser to a server.

## How is it sent?

There are three common ways.

- application/x-www-form-urlencoded (URL-encoded)
- multipart/form-data
- text/plain

### URL encode

1. Convert form data into key/value pairs.
2. Apply URL encoding to those values.

Example:

```
<form method="GET" action="/search">
  <input name="q" value="hello world">
  <input name="page" value="1">
</form>
```

Then it is converted to key-value pairs:

```
q = "hello world"
page = "1"
```

Finally, percent-encode special characters:

```
hello world
↓
hello%20world
```

Some characters are not safe in a URL, so percent encoding is required.

If `GET` is used, the data is attached to the URL query string. If `POST` is used, the data is sent in the request body.

### multipart

This is mainly used to send files.

`multipart/form-data` is a format that sends multiple parts in one body.

Example:

```
<form method="POST" enctype="multipart/form-data">
  <input name="username">
  <input type="file" name="avatar">
</form>
```

Then:

```
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryABC123

Body:
------WebKitFormBoundaryABC123
Content-Disposition: form-data; name="username"

akira
------WebKitFormBoundaryABC123
Content-Disposition: form-data; name="avatar"; filename="cat.png"
Content-Type: image/png

(binary data here)
------WebKitFormBoundaryABC123--
```

URL encoding is not suitable for raw binary data, so `multipart/form-data` is used.

In `(binary data here)`, raw binary bytes are included, such as `FF D8 FF E0 00 10 4A 46 ...`.
