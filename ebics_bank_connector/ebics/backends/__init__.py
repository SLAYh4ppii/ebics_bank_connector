"""Pluggable EBICS backends.

Each backend module exposes a ``create(**kwargs)`` factory returning an
object with the methods used by :class:`ebics_bank_connector.ebics.client.EbicsClient`:

    ping(), send_ini(), send_hia(), fetch_bank_keys(),
    download(order_type, start, end, account), list_accounts()
"""
