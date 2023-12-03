import abc
from typing import Dict, List, Type, Union, Generic, TypeVar, Optional

import pydantic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ReadSchema(BaseModel):
    pass


class ModelReadSchema(ReadSchema, abc.ABC, Generic[T]):
    __model__: Type[T]

    @classmethod
    @abc.abstractmethod
    def from_model(cls, model: T) -> "ModelReadSchema[T]":
        ...


class WriteSchema(BaseModel):
    pass


class ModelWriteSchema(WriteSchema, abc.ABC, Generic[T]):
    __model__: Type[T]

    @abc.abstractmethod
    def to_model(self) -> T:
        ...


class ModelEditSchema(WriteSchema, abc.ABC, Generic[T]):
    __model__: Type[T]

    @abc.abstractmethod
    def apply_changes(self, document: T) -> T:
        """
        Apply changes to the given document.
        NOTE: It does not return a new document, but modifies the given one.

        :param document: Document to modify
        :return: Modified document
        """
        ...
