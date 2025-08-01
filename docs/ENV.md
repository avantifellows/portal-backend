## Environment Variables

### Core Configuration

#### `JWT_SECRET_KEY`
A string of random characters used to encrypt access and refresh tokens. Use different keys for Production and Staging.

#### `DB_SERVICE_URL`
The URL to connect to our database service (e.g., `http://localhost:8000`)

#### `DB_SERVICE_TOKEN`
Token to authenticate with the database service

### Business Logic

#### `DEFAULT_ACADEMIC_YEAR` *(optional)*
The default academic year for student records. Defaults to `"2025-2026"` if not specified.

### AWS Integration

#### `SQS_ACCESS_KEY`, `SQS_SECRET_ACCESS_KEY`
AWS access keys that only allow for SQS actions

#### `AWS_SQS_URL`
The URL to send SQS messages for logging attendance (v1 BQ)
