# Web UI Guide

How to use the browser interface at `http://127.0.0.1:8000`. Start it with:

```bash
python main.py
```

For the REST endpoints behind this UI, see
[API_DOCUMENTATION.md](../API_DOCUMENTATION.md).

---

## Two tabs

The top navigation switches between the two ways to query your papers.

### Semantic Search

Returns the matching passages themselves — no LLM, so it is fast and cheap.

1. Type a query, e.g. *"attention mechanism in transformers"*.
2. Pick how many results you want (3, 5, or 10 — default 5).
3. Optionally narrow **In:** to a single paper, or leave it on *All papers*.
4. Press **Enter** or click the search button.

Each result shows the passage text, its source filename and page, and a match
percentage colored by strength — green above 50%, amber 35–50%, grey below.
Scores are relative to your corpus: 45% may be the best available match in one
collection and mediocre in another, so compare results against each other
rather than against a fixed threshold.

Before your first search the results area offers example queries; clicking one
runs it.



### AI Assistant

Retrieves relevant passages and has an LLM answer from them, citing the papers
it used.

1. Type a question.
2. Press **Enter** to send (**Shift+Enter** inserts a newline).

Two controls sit above the input:

| Control | Effect |
|---|---|
| **Use paper context (RAG)** | On by default. Uncheck to answer from the model's own knowledge without consulting your papers. |
| **Focus on** | Defaults to *All papers*. Pick one to restrict retrieval to that paper only. Only indexed papers are listed. |

Answers list the sources they drew on. Follow-up questions are resolved against
the conversation, so *"what BLEU score did it achieve?"* correctly picks up what
"it" refers to from the previous turn.

**Clear chat** discards this tab's conversation history. Do this when you switch
topics — stale history can otherwise pull a follow-up rewrite off course.
Other tabs are unaffected.

---

## Managing papers

Click **Manage Files** in the AI Assistant tab to open the file manager.

### Adding a paper

Drag a PDF onto the upload area, or click **Browse** to pick one. A progress
bar runs during the transfer, and the file appears in the list when it lands.

**Uploading does not index the file.** A newly uploaded paper is on disk but
not yet searchable — you must process it.

### Processing

Click **Process** on an uploaded file to chunk, embed, and index it. This takes
a few seconds per paper, most of it spent generating embeddings.

Re-processing a paper replaces its previous chunks rather than duplicating
them, so it is safe to run again if you are unsure whether it worked.

Once processed, the paper is available to both tabs and to the MCP tools.

### Selecting

Click **Select** on an indexed file to scope the assistant to that paper. The
chat tab's **Focus on** selector updates to match; choose *All papers* there to
query the whole corpus again.

Papers that are not indexed offer no Select button and do not appear in either
selector, since they cannot be searched. Process them first.

### Understanding the list

Each file shows its size and two badges — where it came from, and whether it is
searchable:

| Badge | Meaning |
|---|---|
| **Existing** | Sits in `data/papers/` |
| **Uploaded** | Sits in `data/uploads/` — added through this UI |
| **Indexed** | Chunked and embedded; searchable now |
| **Not indexed** | On disk only; invisible to search until processed |

Anything marked *Not indexed* gets a **Process** button. An already-indexed
file offers **Reprocess**, which is useful after replacing the PDF with a newer
version.

To check the same thing from the command line:

```bash
python cmd_basis.py list
```

---

## Known limitations

**Chat history is per-tab and in-memory.** Each browser tab gets its own
conversation, and all of them are lost when the server restarts.

**Bulk indexing is command-line only.** The UI processes one paper at a time.
To index a folder of PDFs at once:

```bash
python cmd_basis.py ingest
```

**Deleting papers is not exposed in the UI.** Remove one from the index with
`core.vectorstore.delete_source("name.pdf")`, and delete the PDF from disk
separately.

---

## Troubleshooting

**Search returns nothing**
Nothing is indexed. Confirm with `python cmd_basis.py list`, then run
`python cmd_basis.py ingest`.

**A paper I uploaded is not being found**
Uploading does not index. Look for the **Not indexed** badge on it in the file
manager and click **Process**.

**The assistant answers without using my papers**
Check that **Use paper context (RAG)** is ticked. If it is, and search also
returns nothing, the corpus is empty.

**Selecting a paper returns no answers**
Check its badge in the file manager — if it reads **Not indexed**, process it.

**An error mentions the model does not exist**
Groq retires models regularly. See
[Troubleshooting](../QUICKSTART.md#troubleshooting) for how to list the models
your key can use and update `GROQ_MODEL`.

**Upload fails**
Only `.pdf` files are accepted. Filenames are reduced to a basename, so
directory paths in the name are stripped rather than honored.

**Processing fails with "no text could be extracted"**
The PDF has no text layer — its pages are images, which is normal for scanned
documents and for some exported slide decks. Nothing can index it as-is. Run
it through OCR first:

```bash
ocrmypdf scanned.pdf searchable.pdf
```

Then upload `searchable.pdf`. To check a file before uploading, open it in a
PDF viewer and try to select text: if you cannot, neither can the indexer.
