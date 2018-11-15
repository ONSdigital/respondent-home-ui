import os
import random
import sys
import time

from locust import HttpLocust, TaskSet, task

sys.path.append(os.getcwd())

from tests import get_all_hacs_for_collection_exercise, get_collex_id


class UserBehavior(TaskSet):

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        """
        Load work flow:
        1) generate sample file with N rows
        2) run setup scripts with new sample file
        3) get all hacs from db (that would otherwise go to letter)
        4) use random.choice on hacs when creating a new locust
        """
        self.access_code = random.choice(self.parent.access_codes)

    @task(8)
    def index(self):
        self.client.get("/")

    @task(1)
    def cookies(self):
        self.client.get('/cookies-privacy')

    @task(1)
    def contact(self):
        self.client.get('/contact-us')


class InvalidUserBehaviour(TaskSet):

    @task(8)
    def index(self):
        self.client.get("/")

    @task(2)
    def use_invalid_code(self):
        self.client.post("/?valid=false", {
            'iac1': '1234', 'iac2': '5678', 'iac3': '9012', 'action[save_continue]': '',
        })


class PatientUserBehaviour(UserBehavior):

    @task(4)
    def launch_survey(self):
        self.client.post("/?valid=true", {
            'iac1': self.access_code[:4],
            'iac2': self.access_code[4:8],
            'iac3': self.access_code[8:],
            'action[save_continue]': '',
        })


class ImpatientUserBehaviour(UserBehavior):

    @task(4)
    def launch_survey_impatiently(self):
        self.client.post("/?valid=true&impatient=15s", {
            'iac1': self.access_code[:4],
            'iac2': self.access_code[4:8],
            'iac3': self.access_code[8:],
            'action[save_continue]': '',
        }, timeout=15)


class _BaseRespondent(HttpLocust):
    access_codes = []
    min_wait = 5000
    max_wait = 9000
    task_set = UserBehavior

    @classmethod
    def setup(cls):
        while True:
            cls.access_codes = get_all_hacs_for_collection_exercise(get_collex_id())
            if cls.access_codes:
                break
            time.sleep(2)


class InvalidRespondent(_BaseRespondent):
    task_set = InvalidUserBehaviour
    weight = 1


class PatientRespondent(_BaseRespondent):
    task_set = PatientUserBehaviour
    weight = 2


class ImpatientRespondent(_BaseRespondent):
    task_set = ImpatientUserBehaviour
    weight = 4
