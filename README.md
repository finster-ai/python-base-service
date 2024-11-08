# python-base-service-fastapi-uvicorn

This is a base repo of a Python microservice that provides a REST API, PUB/SUB capabilities and a GRPC API. It is built on top of Flask
TODO: add mongo and redis implementation

The idea behind this repo is to provide a base for a microservice that can be easily clone and extended to provide more functionality.



## Tools, Frameworks Etc

This is all in Python 3.10 and all requirements can be found
in `requirements.txt`.



## Installation

To install the required dependencies run the following:
**NB** make sure you're using python 3.10 - the same version as used in the [Docker image](Dockerfile)

```
pip install -U pip
pip install -r requirements.txt
```



### Running locally

The backend needs access to GCP to run. Before running it for the first time, you need to authenticate running this command in your terminal.
```
gcloud auth application-default login
```
If this doesn't work, please check the documentation <https://cloud.google.com/docs/authentication/provide-credentials-adc>



### Code Structure & Basic Flow

* Endpoints are defined in [`controller.py`]
* GRPC endpoints logic is implemented in [`base_model1_grpc_impl.py`]
* The entry point of the app is in [`api_base_service.py`]
* By default the app starts with a subscriber to a pubsub topic, an REST API server and a GRPC server



### Modifying Proto Files

You need to run this command to generate new  grpc files after proto has been updated
```
python -m grpc_tools.protoc -I./app/proto --python_out=./app/proto/gen --grpc_python_out=./app/proto/gen ./app/proto/BaseModel1.proto
```



### Running the app with Uvicorn
```
uvicorn python_base_service:app --host 0.0.0.0 --port 8080 --workers 1 --timeout-keep-alive 600
```



### Building Image and Pushing to GCR

[//]: # ()
[//]: # (```)

[//]: # (docker buildx build --platform linux/amd64 -t gcr.io/daring-keep-408013/weaviate-upload-service:latest --push .)

[//]: # (```)

[//]: # (and for new dev)
```
docker buildx build --platform linux/amd64 -t us-central1-docker.pkg.dev/finster-ops/registry-docker/api-base-service:latest --push .
```


### Deploying to GKE
```
kubectl apply -f deployment-dev.yaml
```



### Force Redeploy

```
kubectl rollout restart deployment -n dev api-base-service
```



### Delete Service

```
kubectl delete deployment  -n dev api-base-service
```



## Building Image and Running Locally
### Build Image
```
docker build --platform linux/amd64 -t python-base-service:local .
```
### Deploy Image
```
docker run --platform linux/amd64 -d -p 8080:8080 \
--name python-base-service-local \
-v /Users/emmanuelcastillodecarvalho/Finster\ AI/.gke-automation-emmanuel-daring-keep-408013.json:/var/secrets/google/key.json \
-e GOOGLE_APPLICATION_CREDENTIALS="/var/secrets/google/key.json" \
python-base-service:local
```
