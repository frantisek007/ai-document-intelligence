class DocumentProcessingError(Exception):
    pass


class UnsupportedDocumentError(DocumentProcessingError):
    pass


class DocumentTextExtractionError(DocumentProcessingError):
    pass