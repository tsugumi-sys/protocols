## What is Fields in HTTP?

The fields are the place to store metadata and send it to the target within the standarized way.

For example:

```
Content-Type: application/json
Authorization: Bearer xxx
```

Content-Type specifies the data type. The reciever can know it and handle properly.

Why we don't use body to send this metadata?:

The body is free, we can send any bytes. It's usefull for the application, but not for HTTP.
