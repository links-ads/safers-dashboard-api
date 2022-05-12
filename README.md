# safers-gateway
Common API Gateway for SAFERS

This API provides the backend for the safers-dashboard.

## components

### server

Django / Django-Rest-Framework

### auth

FusionAuth

### broker

RabbitMQ

### worker

Pika

### storage

AWS S3

## details

Users can authenticate locally or remotely (via FusionAuth).  Note that only remote users can interact w/ the SAFERS API - so there's really not much point in using the Dashboard as a local user.

The RMQ app uses `pika` to monitor the SAFERS Message Queue.  Upon receipt of a message with a registered routing_key the handlers defined in `rmq.py#BINDING_KEYS` are called.  This typically creates one or more model instances in the Dashboard DB.

## profiling

Profiling is handled using cProfile & django-cprofile-middleware & snakeviz & silk.

- appending `prof` to a URL will give a profile summary (in development only)
- appending `prof&download` to a URL will create a file called "view.prof" which can be inspected by running `snakeviz ./path/to/view.prof` outside of docker
- db queries can be monitored by going to "http://localhost:8000/silk"