from locust import HttpLocust, TaskSet, task


class UserBehavior(TaskSet):

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        # TODO: get an access code
        pass

    def on_stop(self):
        """ on_stop is called when the TaskSet is stopping """
        pass

    @task(8)
    def index(self):
        self.client.get("/")

    @task(1)
    def cookies(self):
        self.client.get('/cookies-privacy')

    @task(1)
    def contact(self):
        self.client.get('/contact-us')

    @task(2)
    def use_invalid_code(self):
        self.client.post("/", {
            'iac1': '1234', 'iac2': '5678', 'iac3': '9012', 'action[save_continue]': '',
        })

    @task(4)
    def launch_survey(self):
        # TOOD: use a "real" access code
        iac = 'dpbdwym6y9pc'
        self.client.post("/", {
            'iac1': iac[:4], 'iac2': iac[4:8], 'iac3': iac[8:], 'action[save_continue]': '',
        })


class Respondent(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
