from __future__ import annotations

from abc import ABC, abstractmethod


class BaseService(ABC):
    def __init__(self, client):
        self.client = client

    @abstractmethod
    def get_all(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, item_id):
        raise NotImplementedError

    @abstractmethod
    def create(self, payload):
        raise NotImplementedError

    @abstractmethod
    def update(self, item_id, payload):
        raise NotImplementedError

    @abstractmethod
    def delete(self, item_id):
        raise NotImplementedError
