## Why is `multipart/form-data` used?

`multipart/form-data` is used when a request needs to send normal form fields and files together.

It allows binary data such as images, PDFs, or other files to be sent in the HTTP request body without converting the file data to Base64.

Each field is sent as a separate part, and each part can have its own headers such as `Content-Disposition` and `Content-Type`.

## How do we send fields and files without `multipart/form-data`?

Without `multipart/form-data`, sending both fields and files becomes less standard and less convenient.

For example:

- With `application/x-www-form-urlencoded`, you can send normal text fields, but it is not suitable for file uploads.
- With `application/json`, you can send structured field data, but files usually need to be encoded as Base64 or uploaded separately.
- You can also send the raw file as the entire request body, but then you cannot naturally include multiple form fields in the same format.

So `multipart/form-data` is commonly used because it lets one HTTP request include both text fields and file data in a standard way.
