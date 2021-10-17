# VMware VeloCloud SD-WAN: Automated Edge Configuration Backup

This Python app is containerised with [Docker Compose](https://docs.docker.com/compose/) for rapid and modular deployment that fits in any microservice architecture.

It does the following:

1. Call the [VMware VeloCloud Orchestrator API](#reference) to download a copy of the config stack for all of the SD-WAN Edges in the enterprise network;
2. Export the config stacks as separate JSON files on a `Docker volume` that is mounted in the same directory of the `docker-compose.yml` file on the Docker host, or in the same directory of the Python script if it is run as a standalone service, in a number of nested directories by the date and time of the API call; and
3. Repeat the process every 15 minutes on the hour and at :15, :30 and :45 past for an automated Edge config backup.

<img src="https://kurtcms.org/git/vco-ent-edge-config/vco-ent-edge-config-screenshot.png" width="550">

## Table of Content

- [Getting Started](#getting-started)
  - [Git Clone](#git-clone)
  - [Environment Variable](#environment-variables)
  - [Crontab](#crontab)
  - [Docker Container](#docker-container)
	  - [Docker Compose](#docker-compose)
	  - [Build and Run](#build-and-run)
  - [Standalone Python Script](#standalone-python-script)
    - [Dependencies](#dependencies)
    - [Cron](#cron)
- [Config Stack in JSON](#config-stack-in-json)
- [Reference](#reference)

## Getting Started

Get started in three simple steps:

1. [Download](#git-clone) a copy of the app;
2. Create the [environment variables](#environment-variables) for the VeloCloud Orchestrator authentication and modify the [crontab](#crontab) if needed;
3. [Docker Compose](#docker-compose) or [build and run](#build-and-run) the image manually to start the app, or alternatively run the Python script as a standalone service.

### Git Clone

Download a copy of the app with `git clone`
```shell
$ git clone https://github.com/kurtcms/vco-ent-edge-config /app/
```

### Environment Variables

The app expects the hostname, username and password for the VeloCloud Orchestrator as environment variables in a `.env` file in the same directory. Be sure to create the `.env` file.

```shell
$ nano /app/.env
```

And define the credentials accordingly.

```
VCO_HOSTNAME = 'vco.managed-sdwan.com/'
VCO_USERNAME = 'kurtcms@gmail.com'
VCO_PASSWORD = '(redacted)'
```

### Crontab

By default the app is scheduled with [cron](https://crontab.guru/) to pull a copy of the config stack for all the SD-WAN Edges in the enterprise network every 15 minutes, with `stdout` and `stderr` redirected to the main process for `Docker logs`.  

Modify the `crontab` if a different schedule is required.

```shell
$ nano /app/crontab
```

### Docker Container

#### Docker Compose

With Docker Compose, the container may be provisioned with a single command. Be sure to have Docker Compose [installed](https://docs.docker.com/compose/install/).

```shell
$ docker-compose up
```

Stopping the container is as simple as a single command.

```shell
$ docker-compose down
```

#### Build and Run

Otherwise the Docker image can also be built manually.

```shell
$ docker build -t vco-ent-edge-config /app/
```

Run the image with Docker once it is ready.  

```shell
$ docker run -it --rm --name vco-ent-edge-config vco-ent-edge-config
```

### Standalone Python Script

#### Dependencies

Alternatively the `vco-ent-edge-config.py` script may be deployed as a standalone service. In which case be sure to install the following required libraries:

1. [Requests](https://github.com/psf/requests)
2. [Python-dotenv](https://github.com/theskumar/python-dotenv)

```shell
$ pip3 install requests python-dotenv
```

The [VeloCloud Orchestrator JSON-RPC API Client](https://github.com/vmwarecode/VeloCloud-Orchestrator-JSON-RPC-API-Client---Python) library is also required. Download it with [wget](https://www.gnu.org/software/wget/).

```shell
$ wget -P /app/ https://raw.githubusercontent.com/vmwarecode/VeloCloud-Orchestrator-JSON-RPC-API-Client---Python/master/client.py
```

#### Cron

The script may then be executed with a task scheduler such as [cron](https://crontab.guru/) that runs it once every 15 minutes for example.

```shell
$ (crontab -l; echo "*/15 * * * * /usr/bin/python3 /app/vco-ent-edge-config.py") | crontab -
```

## Config Stack in JSON

The config stacks for all the Edges in the enterprise network will be downloaded and saved as separate JSON files on a `Docker volume` that is mounted in the same directory of the `docker-compose.yml` file on the Docker host. If the Python script is run as a standalone service, the JSON files will be in the same directory of the script instead.

In any case, the JSON files are stored under a directory by the enterpriseName, and nested in a number of subdirectories named respectively by the year, the month and the day, and finally by the the full date and time of the API call to ease access.

```
.
└── enterpriseName/
    └── Year/
        └── Month/
            └── Date/
                └── YYYY-MM-DD-HH-MM-SS/
                    ├── edgeName1.json
                    ├── edgeName2.json
                    ├── edgeName3.json
                    └── edgeName4.json
```

## Reference

- [VMware SD-WAN Orchestrator API v1 Release 4.0.1](https://code.vmware.com/apis/1045/velocloud-sdwan-vco-api)
