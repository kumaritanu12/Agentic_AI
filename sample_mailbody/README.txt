Practice files:
- email_01.txt: email body with two attachments
- attachments/wafer_probe_results.xlsx: wafer-level results
- attachments/test_summary.docx: test summary

Expected exercise:
1. Parse email_01.txt for Lot ID and Foundry Lot ID.
2. Send each attachment path to your ReAct agent.
3. Agent selects read_excel for XLSX and read_word for DOCX.
4. Print first five Excel rows and first five non-empty Word paragraphs.
