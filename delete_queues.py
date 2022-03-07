from rsmq import RedisSMQ

from ServiceConfig import ServiceConfig

SERVICE_CONFIG = ServiceConfig()

if __name__ == "__main__":
    results_queue = RedisSMQ(
        host=SERVICE_CONFIG.redis_host,
        port=SERVICE_CONFIG.redis_port,
        qname=SERVICE_CONFIG.results_queue_name,
    )

    results_queue.deleteQueue().execute()
    print("queue deleted")
