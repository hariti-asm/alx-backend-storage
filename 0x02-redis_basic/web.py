#!/usr/bin/env python3
"""
web.py: Module to implement the get_page function.
"""

import requests
import redis
from functools import wraps
from typing import Callable

# Connect to Redis server
redis_client = redis.StrictRedis(
        host='localhost',
        port=6379,
        decode_responses=True
        )


def cache_and_count_access(func: Callable) -> Callable:
    """
    Decorator to cache the result of a
    function and count the number of accesses.
    """
    @wraps(func)
    def wrapper(url: str) -> str:
        # Count the number of accesses
        count_key = f"count:{url}"
        current_count = redis_client.incr(count_key)

        # Get the cached result if available
        cache_key = f"cache:{url}"
        cached_result = redis_client.get(cache_key)

        if cached_result:
            return cached_result
        else:
            # Call the original function and cache the result
            result = func(url)
            redis_client.setex(cache_key, 10, result)

            return result

    return wrapper


@cache_and_count_access
def get_page(url: str) -> str:
    """
    Get the HTML content of a URL
    and cache the result with an expiration time of 10 seconds.
    """
    response = requests.get(url)
    return response.text


if __name__ == "__main__":
    # Example usage
    slow_url = "http://slowwly.robertomurray.co.uk/delay/10000/url/http://www.example.com"
    print(get_page(slow_url))
