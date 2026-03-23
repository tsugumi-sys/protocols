## What is the contents in HTTP?

The contents is a data attached to the request. We can send bytes data with the request because HTTP can handle this contents.

In http0.9, we cannot send include data within the request.
But we want to send a data.
In http1.0/1.1, we have a contents (body) in the request.

```
Field1: value
Field2: value
Content-length: bytes

<bytes start>
```
