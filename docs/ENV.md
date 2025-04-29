## Environment Variables

### `JWT_SECRET_KEY`

This is a string of random characters that will be used to encrypt the access and refresh tokens. Make sure to use different keys for Production and Staging.

### `DB_SERVICE_URL`

The URL to connect to our database service

### `DB_SERVICE_TOKEN`

Token to authenticate DB service

### `SQS_ACCESS_KEY`, `SQS_SECRET_ACCESS_KEY`

Access keys that only allow for SQS actions

### `AWS_SQS_URL`

The URL to send SQS message for logging attendance (v1 BQ)
