class AppError(Exception):
    """A controlled failure that is safe to expose through the API."""

    status_code = 500
    code = "internal_error"
    public_message = "The request could not be completed."

    def __init__(self, public_message: str | None = None) -> None:
        super().__init__(public_message or self.public_message)
        if public_message:
            self.public_message = public_message


class InvalidUploadError(AppError):
    status_code = 400
    code = "invalid_upload"
    public_message = "The uploaded file is empty or invalid."


class UnsupportedFileError(AppError):
    status_code = 415
    code = "unsupported_file"
    public_message = "Upload a plain-text .txt file or a text-based .pdf file."


class UploadTooLargeError(AppError):
    status_code = 413
    code = "upload_too_large"


class ObjectNotFoundError(AppError):
    status_code = 404
    code = "not_found"
    public_message = "The requested item was not found."


class StorageConfigurationError(AppError):
    status_code = 503
    code = "storage_not_configured"
    public_message = "Document storage is not configured."


class StorageError(AppError):
    status_code = 502
    code = "storage_unavailable"
    public_message = "Document storage is temporarily unavailable."


class ExtractionError(AppError):
    status_code = 422
    code = "extraction_failed"
    public_message = "No usable text could be extracted from this file."


class VerifierError(AppError):
    status_code = 502
    code = "verifier_unavailable"
    public_message = "The verification service returned an invalid response."


class VerifierTimeoutError(AppError):
    status_code = 504
    code = "verifier_timeout"
    public_message = "The verification service did not respond in time."


class GroundingError(VerifierError):
    code = "invalid_evidence_reference"
    public_message = "The verification service referenced evidence it was not given."
