"""EBICS abstraction layer.

This package isolates the EBICS protocol from the rest of the app.

    connection.py  -> swappable backend factory (default: ebics-python)
    client.py      -> high-level operations (ping, fetch statements, key init)
    parser.py      -> generic ISO 20022 helpers
    camt_parser.py -> CAMT.053 / CAMT.054 transaction parsing

The backend is intentionally pluggable: ``get_connection`` returns an object
that quacks like :class:`EbicsClient` regardless of the underlying library.
"""
