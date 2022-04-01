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

The RMQ app uses `pika` to monitor the SAFERS Message Queue.  Upon receipt of a message a local record of a corresponding artefact may be created in the Dashboard DB.  Those records can be queried/filtered by Dashboard Users to determine which artefacts to retrieve from the SAFERS API.