"""Sample CAMT.053 XML used by the stub backend and the unit tests."""
SAMPLE_CAMT053 = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
  <BkToCstmrStmt>
    <GrpHdr>
      <MsgId>MSG-2026-001</MsgId>
      <CreDtTm>2026-07-31T08:00:00</CreDtTm>
    </GrpHdr>
    <Stmt>
      <Id>STMT-2026-07-31</Id>
      <Acct>
        <Id><IBAN>DE89370400440532013000</IBAN></Id>
        <Ccy>EUR</Ccy>
      </Acct>
      <Ntry>
        <NtryRef>NTRY-001</NtryRef>
        <Amt Ccy="EUR">150.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <Sts>BOOK</Sts>
        <BookgDt><Dt>2026-07-30</Dt></BookgDt>
        <ValDt><Dt>2026-07-31</Dt></ValDt>
        <AcctSvcrRef>ASR-001</AcctSvcrRef>
        <NtryDtls>
          <TxDtls>
            <RltdPties>
              <Cdtr><Nm>Max Mustermann</Nm></Cdtr>
              <CdtrAcct><Id><IBAN>DE12500105170648489890</IBAN></Id></CdtrAcct>
              <CdtrAgt><FinInstnId><BIC>COBADEFFXXX</BIC></FinInstnId></CdtrAgt>
            </RltdPties>
            <RmtInf>
              <Ustrd>Rechnung RE-2026-001</Ustrd>
              <Ustrd>Vielen Dank</Ustrd>
            </RmtInf>
            <Refs>
              <EndToEndId>E2E-001</EndToEndId>
            </Refs>
          </TxDtls>
        </NtryDtls>
      </Ntry>
      <Ntry>
        <NtryRef>NTRY-002</NtryRef>
        <Amt Ccy="EUR">42.10</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <Sts>BOOK</Sts>
        <BookgDt><Dt>2026-07-30</Dt></BookgDt>
        <ValDt><Dt>2026-07-31</Dt></ValDt>
        <AcctSvcrRef>ASR-002</AcctSvcrRef>
        <NtryDtls>
          <TxDtls>
            <RltdPties>
              <Dbtr><Nm>Lieferant GmbH</Nm></Dbtr>
              <DbtrAcct><Id><IBAN>DE71500105170648489890</IBAN></Id></DbtrAcct>
            </RltdPties>
            <RmtInf>
              <Ustrd>Rechnung RE-2026-002 Lieferant</Ustrd>
            </RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
"""
