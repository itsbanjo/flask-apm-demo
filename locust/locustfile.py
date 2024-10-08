# locust/locustfile.py

from locust import HttpUser, task, between

class OrderUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    @task(1)
    def place_order(self):
        payload = {
            "user_id": "user123",
            "product_id": "1",
            "quantity": 1,
            "region": "North America",
            "device_type": "Desktop"
        }
        headers = {
            "X-User-Region": payload["region"],
            "X-Device-Type": payload["device_type"]
        }
        with self.client.post("/order", data=payload, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")


    @task(2)
    def place_order_broken(self):
        # New payload with different parameters
        payload = {
            "user_id": "findme",
            "product_id": "ifyoucan",
            "quantity": 2,
            "region": "Europe",
            "device_type": "Mobile"
        }
        headers = {
            "X-User-Region": payload["region"],
            "X-Device-Type": payload["device_type"]
        }
        with self.client.post("/order", json=payload, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")

    @task(3)
    def place_order_sluggish(self):
        payload = {
            "user_id": "1",
            "product_id": "1",
            "quantity": 1,
            "region": "North America",
            "device_type": "Desktop",
            "high_latency": "true"
        }
        headers = {
            "X-User-Region": payload["region"],
            "X-Device-Type": payload["device_type"],
            "X-High-Latency": payload["high_latency"],
        }
        with self.client.post("/order", data=payload, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
