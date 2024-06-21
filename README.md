# API-base-service

This is our repo for all our backend code.
This is mission critical code and we'd like to approach full production maintenance as we move from early releases to v1.

## Tools, Frameworks Etc

This is all in Python 3.10 and all requirements can be found
in `requirements.txt`.

We use `pytorch` for the machine learning parts of the codebase.

## Installation

To install the required dependencies run the following:

**NB** make sure you're using python 3.10 - the same version as used in the [Docker image](Dockerfile)

```python -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### Running locally

The backend needs access to GCP to run. Before running it for the first time, you need to authenticate running this command in your terminal.
```
gcloud auth application-default login
```
If this doesn't work, please check the documentation <https://cloud.google.com/docs/authentication/provide-credentials-adc>



To run the server locally: `python main.py`

Check it out: `http://localhost:8080`

Run Locally with Docker:

```
docker build --tag <tag> .
docker run -it -ePORT=8080 -p8080:8080 <>
```

### Testing

To run all unit tests:

```
pytest -o log_cli=True tests/
```

### Code Structure & Basic Flow

* The [`main.py`](https://github.com/finster-ai/data-feed/blob/dev/main.py) file contains a list of API's which will be accessible by the user and is built using `Flask`.
* This file will direct the user's query to an agent (LLM) located in [`agent.py`](https://github.com/finster-ai/data-feed/blob/main/agent.py).
* Based on the query, the agent will call functions exposed by individual clients located in the [`clients`](https://github.com/finster-ai/data-feed/tree/dev/clients) folder.
* Example clients include [`SBTIClient`](https://github.com/finster-ai/data-feed/blob/dev/clients/sbti.py#L17), [`WorldBankClient`](https://github.com/finster-ai/data-feed/blob/dev/clients/worldbank.py#L15) and [`FileClient`](https://github.com/finster-ai/data-feed/blob/dev/clients/files.py#L28).
* Each client will internally call its respective data source which can be through access to files or third-party APIs. The clients contain retrieval logic based on input queries.
* The agent processes outputs from individual clients to produce the output shown to user.
