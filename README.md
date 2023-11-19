# Portal Backend

The backend for Portal created using FastAPI! The frontend can be found [here](https://github.com/avantifellows/Portal).

## Installation

- Create a virtual environment (make sure that `virtualenv` is installed on your system):

```bash
virtualenv venv
```

- Activate the environment:

```bash
source venv/bin/activate
```

- Install the dependencies:

```bash
pip install -r app/requirements.txt
```

- Install `pre-commit`

```
pip install pre-commit
```

- Set up `pre-commit`

```
pre-commit install
```

- Copy `.env.example` to `.env` and set all the environment variables as mentioned in [`docs/ENV.md`](docs/ENV.md).

## Running locally

Simply run:

```
cd app; uvicorn main:app --reload
```

You should see a message like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [98098] using watchgod
INFO:     Started server process [98100]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:58550 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:58550 - "GET /openapi.json HTTP/1.1" 200 OK
```

Use `http://127.0.0.1:8000` as the base URL of the endpoints and navigate to `http://127.0.0.1:8000/docs` to see the auto-generated docs! :dancer:

## Deployment

We are deploying our FastAPI instance on AWS Lambda which is triggered via an API Gateway. In order to automate the process, we are using [AWS SAM](https://www.youtube.com/watch?v=tA9IIGR6XFo&ab_channel=JavaHomeCloud), which creates the stack required for the deployment and updates it as needed with just a couple of commands and without having to do anything manually on the AWS GUI. Refer to [this](https://www.eliasbrange.dev/posts/deploy-fastapi-on-aws-part-1-lambda-api-gateway/) blog post for more details.

The actual deployment happens through Github Actions. Look at [`.github/workflows/deploy_to_staging.yml`](.github/workflows/deploy_to_staging.yml) for understanding the deployment to `Staging` and [`.github/workflows/deploy_to_prod.yml`](.github/workflows/deploy_to_prod.yml) for `Production`. Make sure to set all the environment variables mentioned in [`docs/ENV.md`](docs/ENV.md) in the `Production` and `Staging` environments in your Github repository.
