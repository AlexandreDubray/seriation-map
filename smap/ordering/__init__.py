from abc import ABCMeta, abstractmethod

class OrderingMethod(metaclass=ABCMeta):

    def __init__(self):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def clustering(self) -> bool:
        pass

    @abstractmethod
    def get_order(self, data) -> list[int]:
        pass
