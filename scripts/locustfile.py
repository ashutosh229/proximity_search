import random
from locust import HttpUser, between, task


class User(HttpUser):
    wait_time = between(0, 0.1)

    @task
    def search(self):
        self.client.post(
            "/IP/search/",
            data=dict(
                lat=random.random(),
                long=random.random(),
                cat=random.choice(
                    ["bank", "hospital", "restaurant", "school", "pharmacy"]
                ),
                rad=random.choice([0.1, 0.2, 0.4]),
                link="link.txt",
            ),
        )
