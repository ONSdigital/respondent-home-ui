class InactiveCaseError(Exception):
    """Raised when a user enters a used IAC code"""


class InvalidEqPayLoad(Exception):

    def __init__(self, message):
        super().__init__()
        self.message = message


class InvalidIACError(Exception):
    """Raised when the IAC Service returns a 404"""


class ExerciseClosedError(Exception):
    """Raised when a user attempts to access an already ended CE"""

    def __init__(self, collection_exercise_id):
        super().__init__()
        self.collection_exercise_id = collection_exercise_id
