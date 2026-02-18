"""Abstract base class for generation-specific save file parsers."""

from abc import ABC, abstractmethod

from pokesave.models import SaveFile


class BaseParser(ABC):
    """Base parser that all generation-specific parsers must implement.

    Each parser is responsible for:
    - Parsing the raw save file bytes into a structured SaveFile model
    - Validating the save file's checksum(s)
    - Detecting the specific game version within the generation
    """

    @abstractmethod
    def parse(self, data: bytes) -> SaveFile:
        """Parse raw save file bytes into a structured SaveFile model.

        Args:
            data: The complete raw bytes of the save file.

        Returns:
            A fully populated SaveFile model.

        Raises:
            ValueError: If the data cannot be parsed.
        """
        ...

    @abstractmethod
    def validate_checksum(self, data: bytes) -> bool:
        """Validate the save file's integrity checksum(s).

        Args:
            data: The complete raw bytes of the save file.

        Returns:
            True if all checksums pass, False otherwise.
        """
        ...

    @abstractmethod
    def detect_version(self, data: bytes) -> str:
        """Detect the specific game version from the save data.

        For example, within Gen 3 this distinguishes between
        Ruby, Sapphire, Emerald, FireRed, and LeafGreen.

        Args:
            data: The complete raw bytes of the save file.

        Returns:
            A human-readable game name string (e.g., "Emerald", "Crystal").
        """
        ...
