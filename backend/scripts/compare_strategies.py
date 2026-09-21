## Objective: Compare the performance of different feed strategies (fanout, cacheaside, nocache) by measuring the time taken to fetch the feed for a user.
## compose exec api python scripts/compare_strategies.py

## TEST USER

import time 
import requests 

FOLLOWER_ID = "d220cbf2-d52f-4230-8c63-9be15ff2fb5e"

FOLLOWING_ID = "009e7cbf-d407-4cdd-9475-54338cff7454"

API_BASE_URL = "http://localhost:5000"

## different strategies to test (name, params)
strategies = [
    ("fanout", {"strategy": "fanout", "userId": FOLLOWER_ID}),
    ("cacheaside", {"strategy": "cacheaside", "userId": FOLLOWER_ID}),
    ("nocache", {"strategy": "nocache", "userId": FOLLOWER_ID}),
]

## feed request  
def poll(strategy_name, params, expected_post_id=None) -> tuple[float, bool]: 
    start_time = time.time()
    response = requests.get(f"{API_BASE_URL}/feed", params=params)
    latency_ms = (time.time() - start_time) * 1000

    if response.status_code != 200:
        print(f"Error fetching feed for strategy {strategy_name}: {response.status_code} - {response.text}")
        return latency_ms, False

    # Check if the test post is in the response
    has_test_post = any(post.get("id") == expected_post_id for post in response.json()["items"])
    return latency_ms, has_test_post

## TODO: post creation request
def create_test_post() -> str | None: 
    post_data = {
        "author_id": FOLLOWING_ID,
        "content": "This is a test post by Alice, for performance comparison."
    }
    response = requests.post(f"{API_BASE_URL}/posts", json=post_data)
    # print('RESPONSE', response.json())
    return response.json()['id']
## TODO: main loop 

results = []
for (strategy_name, params) in strategies:
    post_id = create_test_post()

    if post_id is None:
        print(f"Failed to create test post for strategy {strategy_name}. Skipping.")
        continue

    latency_ms, has_test_post = poll(strategy_name, params, expected_post_id=post_id)
    latency_ms2, has_test_post2 = poll(strategy_name, params, expected_post_id=post_id)

    print(f"Strategy: {strategy_name}, Latency: {latency_ms:.2f} ms, Test Post Present: {has_test_post}")
    print(f"Strategy: {strategy_name}, Latency: {latency_ms2:.2f} ms, Test Post Present: {has_test_post2}")
## LOG
