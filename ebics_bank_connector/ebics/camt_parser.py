# Copyright (c) 2026, EBICS Bank Connector
"""CAMT.053 / CAMT.054 transaction parser.

Namespace-agnostic parser that turns a CAMT.053 (bank statement) or
CAMT.054 (debit/credit notification) document into a list of
:class:`Transaction` dataclass-like dicts ready to be imported into
ERPNext ``Bank Transaction`` records.

Each transaction dict contains:

    transaction_id   -> bank-side unique id (used for dedup cursor)
    entry_id         -> NtryRef / account servicer reference
    value_date       -> booking date (Wertstellung)
    posting_date     -> transaction date (Buchung)
    amount           -> signed Decimal (credit +, debit -)
    currency         -> ISO currency
    iban             -> counterparty IBAN (if present)
    bic               -> counterparty BIC (if present)
    counterparty_name-> name of the counterparty
    description      -> full remittance information (Verwendungszweck)
    reference        -> EndToEndId / RmtId
    account_servicer_ref -> Account Servicer Reference (AcctSvcrRef)
    bank_account_iban -> the account the statement belongs to
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from ebics_bank_connector.ebics.parser import (
    find,
    findall,
    local,
    parse_amount,
    parse_date,
    parse_xml,
    text,
)


@dataclass
class Transaction:
    transaction_id: str = ""
    entry_id: str = ""
    value_date: Optional[datetime] = None
    posting_date: Optional[datetime] = None
    amount: Decimal = Decimal("0")
    currency: str = ""
    iban: str = ""
    bic: str = ""
    counterparty_name: str = ""
    description: str = ""
    reference: str = ""
    account_servicer_ref: str = ""
    bank_account_iban: str = ""
    bank_account_currency: str = ""

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "entry_id": self.entry_id,
            "value_date": self.value_date,
            "posting_date": self.posting_date,
            "amount": str(self.amount),
            "currency": self.currency,
            "iban": self.iban,
            "bic": self.bic,
            "counterparty_name": self.counterparty_name,
            "description": self.description,
            "reference": self.reference,
            "account_servicer_ref": self.account_servicer_ref,
            "bank_account_iban": self.bank_account_iban,
            "bank_account_currency": self.bank_account_currency,
        }


def parse_camt(xml: bytes) -> List[Transaction]:
    """Parse a CAMT.053 or CAMT.054 document into :class:`Transaction` list."""
    root = parse_xml(xml)
    transactions: List[Transaction] = []

    # Statement level (BkToCstmrStmt / BkToCstmrAcctRpt)
    for stmt in _iter_statements(root):
        account_iban, account_currency = _account_identification(stmt)
        for ntry in _iter_entries(stmt):
            tx = _parse_entry(ntry)
            if tx is None:
                continue
            tx.bank_account_iban = account_iban
            tx.bank_account_currency = account_currency or tx.currency
            transactions.append(tx)

    return transactions


def _iter_statements(root):
    # CAMT.053: Stmt ; CAMT.054: Ntfctn -> both contain Ntry
    return [s for s in root.iter() if local(s.tag) in ("Stmt", "Ntfctn")]


def _iter_entries(stmt):
    return [n for n in stmt.iter() if local(n.tag) == "Ntry"]


def _account_identification(stmt) -> tuple:
    acct = find(stmt, "Acct")
    iban = ""
    currency = ""
    if acct is not None:
        id_node = find(acct, "Id")
        iban_node = find(id_node, "IBAN") if id_node is not None else None
        iban = text(iban_node) or ""
        ccy_node = find(acct, "Ccy")
        currency = text(ccy_node) or ""
    return iban, currency


def _parse_entry(ntry) -> Optional[Transaction]:
    tx = Transaction()

    # amount + sign
    amt_node = find(ntry, "Amt")
    cdt_dbt = find(ntry, "CdtDbtInd")
    sign = -1 if (text(cdt_dbt) == "DBIT") else 1
    tx.amount = parse_amount(text(amt_node)) * sign
    ccy = amt_node.get("Ccy") if amt_node is not None else None
    tx.currency = ccy or ""

    # dates
    tx.value_date = parse_date(text(find(ntry, "ValDt", "Dt")))
    tx.posting_date = parse_date(text(find(ntry, "BookgDt", "Dt"))) or tx.value_date

    # references
    tx.entry_id = text(find(ntry, "NtryRef")) or ""
    tx.account_servicer_ref = text(find(ntry, "AcctSvcrRef")) or ""
    tx.transaction_id = tx.account_servicer_ref or tx.entry_id or ""

    # status: only booked entries are imported (BOOK)
    status = text(find(ntry, "Sts"))
    if status and status.upper() != "BOOK":
        return None

    # detail level (TxDtls) carries counterparty + remittance info
    details = [d for d in ntry.iter() if local(d.tag) == "TxDtls"]
    if not details:
        return tx

    # use the first detail block (multi-detail entries are rare for our scope)
    dtl = details[0]

    # counterparty
    rltd = find(dtl, "RltdPties")
    if rltd is not None:
        # counterparty IBAN
        for iban_node in rltd.iter():
            if local(iban_node.tag) == "IBAN":
                tx.iban = text(iban_node) or tx.iban
                break
        # counterparty name (Nm under Cdtr/Nm or Dbtr/Nm)
        for nm in rltd.iter():
            if local(nm.tag) == "Nm":
                tx.counterparty_name = text(nm) or tx.counterparty_name
                break
        # BIC
        for fin in rltd.iter():
            if local(fin.tag) == "BIC":
                tx.bic = text(fin) or tx.bic
                break

    # references / remittance information
    rmt_inf = find(dtl, "RmtInf")
    if rmt_inf is not None:
        ustrds = [text(u) for u in rmt_inf.iter() if local(u.tag) == "Ustrd"]
        tx.description = " ".join(filter(None, ustrds))

    refs = find(dtl, "Refs")
    if refs is not None:
        tx.reference = (
            text(find(refs, "EndToEndId"))
            or text(find(refs, "MndtId"))
            or text(find(refs, "PmtInfId"))
            or ""
        )

    # transaction id at detail level overrides entry level if present
    tx.transaction_id = tx.transaction_id or text(find(dtl, "PrtryRef", "Ref")) or ""

    return tx
