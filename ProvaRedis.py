#!/usr/bin/env python3
#prova
import redis

redis_host = "127.0.0.1"
redis_port = 6379
redis_password = ""


def hello_redis():
    try:

        r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

        r.set("msg:hello", "Hello Redis!!!")

        msg = r.get("msg:hello")
        print(msg)

    except Exception as e:
        print(e)


if __name__ == '__main__':
    hello_redis()