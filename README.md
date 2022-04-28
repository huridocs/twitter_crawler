<h3 align="center">Twitter crawler</h3>

---

## Contents

- [Dependencies](#dependencies)
- [Docker containers](#docker-containers)
- [How to use it](#how-to-use-it)
- [HTTP server](#http-server)
- [Queue processor](#queue-processor)
- [Service configuration](#service-configuration)
- [Get service logs](#get-service-logs)
- [Set up environment for development](#set-up-environment-for-development)
- [Execute tests](#execute-tests)

## Dependencies
* Docker 20.10.14 [install link](https://runnable.com/docker/getting-started/)
* Docker-compose 2.4.1 

    Note: On mac Docker-compose is installed with Docker

    [install link](https://docs.docker.com/compose/install/) 

    [install on Ubuntu link](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04)


## Docker containers

A redis server is needed to use the service asynchronously. For that matter, it can be used the 
command `./run start:testing` that has a built-in 
redis server.

Containers with `./run start`

![Alt logo](readme_pictures/docker_compose_up.png?raw=true "docker-compose up")

Containers with `./run start:testing`

![Alt logo](readme_pictures/docker_compose_redis.png?raw=true "docker-compose -f docker-compose-service-with-redis.yml up")

## How to use it

1. Add the Twitter key to the configuration file `src/config.yml`


    twitter_bearer_token: [TOKEN]
2. Start the service with docker compose

```bash
./run start
```
    

3. Add a message to the tasks redis queue with the following format


    queue = RedisSMQ(host='127.0.0.1', port='6579', qname='twitter_crawler_tasks', quiet=False)
    queue.sendMessage(delay=0).message('{"tenant": "tenant_name", "task": "get_tweet", "params": {"query": "@user_handler or #hashtag", "tweets_languages": ["en"]}}').execute()

4. Get results from the results queue


    queue = RedisSMQ(host='127.0.0.1', port='6579', qname='twitter_crawler_results', quiet=False)
    results_message = queue.receiveMessage().exceptions(False).execute()


    # Each crawled tweet is placed in the results queue as a json with the following format

    # { "tenant": "str"
    # "task": "str"
    # "params":   {"created_at": "int",
    #                 "user": {
    #                             "author_id": "int",
    #                             "name": "str",
    #                             "alias": "str",
    #                             "display_name": "str",
    #                             "url": "str",
    #                          },
    #                 "text": str,
    #                 "images_urls": List[str],
    #                 "source": "str",
    #                 "hashtags": List[str],
    #                 "title": "str",
    #                 "tweet_id": "int"},
    # "success": "bool",
    # "error_message": "str",
    # "data_url": "str",
    # "file_url": "str"
    #  }
    


5. Stop the service

```bash
./run stop
```

## Queue processor

The container `Queue processor` is coded using Python 3.9, and it is on charge of the communication with redis.

The code can be founded in the file `QueueProcessor.py` and it uses the library `RedisSMQ` to interact with the redis
queues.

## Service configuration

A configuration file could be provided to set the redis server parameters and the twitter bearer token. 
If a configuration is not provided, the defaults values are used.

The configuration could be manually created, or it can be used the following script:

    python3 -m pip install graypy~=2.1.0 PyYAML~=5.4.1
    python3 ServiceConfig.py

Configuration file name: `src/config.yml`

Default parameters:

    twitter_bearer_token: 
    redis_host: 127.0.0.1
    redis_port: 6379
    mongo_host: 127.0.0.1
    mongo_port: 29017
    graylog_ip: 

## Get service logs

The service logs are stored by default in the files `docker_volume/redis_tasks.log` and `docker_volume/redis_tasks.log`

To use a graylog server, add the following line to the `config.yml` file:

    graylog_ip: [ip]

## Set up environment for development

It works with Python 3.9 [install] (https://runnable.com/docker/getting-started/)

    ./run install_venv

## Execute tests

    ./run test