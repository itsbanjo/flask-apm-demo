# locust/locustfile.py

from locust import HttpUser, task, between

class OrderUser(HttpUser):
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks

    @task
    def place_order(self):
        payload = {
            "user_id": "user123",
            "product_id": "prod456",
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

