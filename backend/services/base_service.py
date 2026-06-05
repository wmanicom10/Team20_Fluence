from __future__ import annotations

from abc import ABC, abstractmethod


class BaseService(ABC):
    """Abstract service interface for shared CRUD behavior.

    This class demonstrates abstraction by defining the operations every
    concrete backend service must implement without prescribing the query or
    validation details of each resource.
    """

    def __init__(self, client):
        self.client = client

    @abstractmethod
    def get_all(self, *args, **kwargs):
        """Define the interface for loading a collection of records."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, item_id):
        """Define the interface for loading one record by its identifier."""
        raise NotImplementedError

    @abstractmethod
    def create(self, payload):
        """Define the interface for creating a new record."""
        raise NotImplementedError

    @abstractmethod
    def update(self, item_id, payload):
        """Define the interface for updating an existing record."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, item_id):
        """Define the interface for deleting an existing record."""
        raise NotImplementedError
