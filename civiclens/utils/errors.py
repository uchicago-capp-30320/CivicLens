class TooFewTopics(Exception):
    def __init__(self, message: str = "Not enough topics generated"):
        self.message = message
        super().__init__(self.message)


class TopicModelFailure(Exception):
    def __init__(self, error: str):
        self.error = error
        self.message = f"Topic modeling failure due to exteral error: {self.error}"
        super().__init__(self.message)
