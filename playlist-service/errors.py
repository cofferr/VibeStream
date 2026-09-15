"""Re-exporta el manejo de errores compartido (vibestream_common.errors)
para no romper los imports existentes de este servicio."""

from vibestream_common.errors import RepositoryError, handle_errors

__all__ = ["RepositoryError", "handle_errors"]
