from abc import abstractmethod, ABC

class LLM(ABC):
    @abstractmethod
    def generate_sql(self, prompt: str) -> str:
        pass



