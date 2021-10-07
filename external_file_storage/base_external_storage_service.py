import abc
import typing


class BaseExternalStorageService(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def store_file_content(self, content: bytes, target_filepath: str, **kwargs) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def list_files(self, target_directory: str, **kwargs) -> typing.Any:
        raise NotImplementedError
