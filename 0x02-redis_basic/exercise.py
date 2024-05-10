#!/usr/bin/env python3
"""
Module for Cache class
"""
import redis
import uuid
from typing import Union, Callable
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator to count the number of calls to a method.

    Args:
        method (Callable): The method to be decorated.

    Returns:
        Callable: The decorated method.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)

    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator to store the history of inputs and outputs.

    Args:
        method (Callable): The method to be decorated.

    Returns:
        Callable: The decorated method.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key_inputs = "{}:inputs".format(method.__qualname__)
        key_outputs = "{}:outputs".format(method.__qualname__)

        # Append the input arguments to the input list
        self._redis.rpush(key_inputs, str(args))

        # Execute the wrapped function to retrieve the output
        output = method(self, *args, **kwargs)

        # Store the output in the output list
        self._redis.rpush(key_outputs, output)

        return output

    return wrapper


class Cache:
    """
    Cache class for storing and retrieving data in/from Redis
    """

    def __init__(self):
        """
        Initializes a new instance of the Cache class.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Stores the input data in Redis using a random key generated with uuid.

        Args:
            data (Union[str, bytes, int, float]): The data to be stored.

        Returns:
            str: The randomly generated key used for storing the data in Redis.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(
            self,
            key: str,
            fn: Callable = None
            ) -> Union[str, bytes, int, float, None]:
        """
        Retrieves the data stored in Redis using the given key.

        Args:
            key (str): The key used to retrieve the data from Redis.
            fn (Callable, optional): A callable function to
            convert the data back to the desired format.

        Returns:
            Union[str, bytes, int, float, None]: The retrieved data.
        """
        data = self._redis.get(key)

        if data is None:
            return None

        return fn(data) if fn else data

    def get_str(self, key: str) -> Union[str, None]:
        """
        Retrieves and converts the data stored in Redis as a UTF-8 string.

        Args:
            key (str): The key used to retrieve the data from Redis.

        Returns:
            Union[str, None]: The retrieved data as a UTF-8 string.
        """
        return self.get(key, fn=lambda d: d.decode("utf-8"))

    def get_int(self, key: str) -> Union[int, None]:
        """
        Retrieves and converts the data stored in Redis as an integer.

        Args:
            key (str): The key used to retrieve the data from Redis.

        Returns:
            Union[int, None]: The retrieved data as an integer.
        """
        return self.get(key, fn=int)


def replay(func: Callable):
    """
    Displays the history of calls for a particular function.

    Args:
        func (Callable): The function for which the history
        needs to be displayed.
    """
    key_inputs = "{}:inputs".format(func.__qualname__)
    key_outputs = "{}:outputs".format(func.__qualname__)

    inputs = [eval(args) for args in cache._redis.lrange(key_inputs, 0, -1)]
    outputs = cache._redis.lrange(key_outputs, 0, -1)

    print("{} was called {} times:".format(func.__qualname__, len(inputs)))
    for args, output in zip(inputs, outputs):
        print("{}{} -> {}".format(
            func.__qualname__,
            args,
            output.decode("utf-8")))
