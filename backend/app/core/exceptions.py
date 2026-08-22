class AppError(Exception):
    """Base class for application-level errors raised by services and repositories."""


class RepositoryError(AppError):
    pass


class DocumentNotFoundError(RepositoryError):
    def __init__(self, collection: str, identifier: str):
        self.collection = collection
        self.identifier = identifier
        super().__init__(f"{collection} document '{identifier}' was not found")


class DuplicateDocumentError(RepositoryError):
    def __init__(self, collection: str, detail: str = ""):
        self.collection = collection
        super().__init__(f"Duplicate document in '{collection}': {detail}")


class UnauthorizedAccessError(AppError):
    def __init__(self, detail: str = "You do not have access to this resource"):
        super().__init__(detail)


class ValidationFailedError(AppError):
    pass
