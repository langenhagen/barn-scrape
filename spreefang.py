"""
Scrape from res.cloudinary.com/spreefang-ug

100 requests happen in about 10s

36**20 requests are 13367494538843734067838845976576.
That may take endles years to finish.

See: https://docs.python.org/2/library/itertools.html
"""
import itertools
import http.client
import random
import time

import grequests

ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyx'

print(f"> {36**20} possibilites...")


def sanity_check():
    """Should the word jpchblp7zzpcei0qvima should work."""
    connection = http.client.HTTPSConnection("res.cloudinary.com")
    for word in ['jpchblp7zzpcei0qvima']:

        connection.request("GET", f"/spreefang-ug/image/upload/{word}.jpg")
        response = connection.getresponse()
        if response.getcode() == 200:
            print(f"> OK: Sanity checked catch at: {word}")
        else:
            raise ValueError("Sanity Check Failed")

    connection.close()


def scrape_brute_force():
    """
    Scrape via brute force from 0 to last.

    Its the faster approach, but would take countless years to iterate over all
    combinations.
    """
    connection = http.client.HTTPSConnection("res.cloudinary.com")
    start_time = time.time()
    for i, word in enumerate(itertools.product(ALPHABET, repeat=20)):
        if i < 16000:
            # speed things up due to manual prior runs without result
            continue

        if i % 100 == 0:
            elapsed_seconds = int(time.time() - start_time)
            print(
                f"> {i} aka {''.join(word)} "
                f"elapsed time: {elapsed_seconds}s..."
            )

        connection.request("GET", f"/spreefang-ug/image/upload/{word}.jpg")
        response = connection.getresponse()
        if response.getcode() == 200:
            print(f"> Catch at: {word}")
            data = response.read()
            with open(f"{word}.jpg", 'wb') as file:
                file.write(data)

    connection.close()


def scrape_random():
    """
    Scrape infinitely with random words.

    It's the slower approach, but, depending on the density of the data,
    It might just work.
    """
    start_time = time.time()
    i = 0
    while True:
        i += 1
        word = "".join(random.choice(ALPHABET) for _ in range(20))

        if i % 100 == 0:
            elapsed_seconds = int(time.time() - start_time)
            print(
                f"> {i} aka {''.join(word)} "
                f"elapsed time: {elapsed_seconds}s..."
            )

        connection = http.client.HTTPSConnection("res.cloudinary.com")
        connection.request("GET", f"/spreefang-ug/image/upload/{word}.jpg")
        response = connection.getresponse()
        if response.getcode() == 200:
            print(f"> Catch at: {word}")
            data = response.read()
            with open(f"{word}.jpg", 'wb') as file:
                file.write(data)

    connection.close()


def cb_grequests_exception_handler(request, exception):
    """Exception handler for asynchronous grequests call."""
    pass


def scrape_random_grequests():
    """
    Scrape infinitely with random words using asynchronous grequests.

    By far the  fastest approach, depending on the density of the data,
    It might just work, although it might still be too little
    """
    n_parallel_requests = 400  # ~400 costs like 1.4 GB RAM

    i = 0
    start_time = time.time()
    while True:
        i += n_parallel_requests

        request_chunk = []
        url_prefix = "https://res.cloudinary.com/spreefang-ug/image/upload"
        for _ in range(n_parallel_requests):
            word = "".join(random.choice(ALPHABET) for _ in range(20))
            url = f"{url_prefix}/{word}.jpg"
            request_chunk.append(grequests.get(url))

        responses = grequests.map(
            request_chunk,
            exception_handler=cb_grequests_exception_handler
        )
        catch_responses = [x for x in responses if x is not None]

        elapsed_seconds = int(time.time() - start_time)
        print(f"> {i} requests; elapsed time: {elapsed_seconds}s...")

        for response in catch_responses:
            if response.status_code == 200:
                print(f"> Catch at: {word}")
                with open(f"{word}.jpg", 'wb') as file:
                    file.write(response.content)


if __name__ == '__main__':
    sanity_check()
    # scrape_brute_force()
    # scrape_random()
    scrape_random_grequests()
