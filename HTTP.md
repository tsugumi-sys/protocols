# HTTP Basics

## Four data containers in modern HTTP (HTTP/1.x, HTTP/2, HTTP/3)

- method and path
- fields (headers)
- content (body)
- status

Each method has its own semantics. For example, you generally cannot send a request body with the GET method. Technically it can be sent, but many systems restrict or ignore it.

Important note: HTTP/0.9 was much simpler. It was basically only `GET` + path in the request, and only a body in the response (no status line, no headers).

In older HTTP, a resource was mostly just a web page that you fetched by URL.
Nowadays, HTTP handles many types of data, not only pages.

In modern HTTP, request and response are usually explained like this:

- Request: method, path/target, headers, optional body
- Response: status, headers, optional body

Simple example:
- `GET /users/42` requests a user resource.
- The server may return `200 OK` with a JSON body.

The core functionality of HTTP is managing data over a network (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, etc.).
HTTP is the protocol that standardizes this exchange, similar to CRUD-oriented applications.
