# RAG chatbot in Python (free, local)

Code for the ADITEJUS tutorial **"RAG Tutorial for Beginners: Build a Chatbot in Python, Free (2026)"**. It's a chatbot that answers questions from your own PDFs and text files, and names the file it used. It runs on your laptop with Ollama and ChromaDB, with no API key and no bill.

- Video: on the ADITEJUS channel, https://www.youtube.com/@aditejus (the tutorial publishes Sat 31 Oct 2026)
- Go deeper (free, 1 hour): Complete RAG Course for Beginners, https://youtu.be/C23OIVPeodU

## Setup (4 steps)

1. Install Ollama from https://ollama.com
2. Pull the two models:
   ```
   ollama pull nomic-embed-text
   ollama pull qwen2.5:3b
   ```
3. Install the Python packages (pinned to the versions used in the video):
   ```
   pip install -r requirements.txt
   ```
4. Put your files in the `docs` folder (three made-up sample files are included), then run:
   ```
   python3 rag_chat.py index docs      # read, chunk, embed and store your files
   python3 rag_chat.py chat            # ask questions (empty line to quit)
   ```

## Notes

- **Re-indexing:** `rag_chat.py` removes a file's old chunks before storing new ones. If you change the chunking code, you can also delete the `rag_db` folder and re-index from scratch, which is what the video does.
- **The mistake from the video:** `python3 rag_chat.py index docs --naive` cuts the text every 80 characters. That splits "up to 5 days" from "carry over to the next year", and the answer loses the number. The default chunker keeps whole paragraphs with a one-paragraph overlap.
- `python3 rag_chat.py chat --show` prints the chunks the search found. That's the fastest way to debug a RAG app.
- **Scanned PDFs** have no text layer, so they come out empty and are skipped. Run OCR first (for example with `ocrmypdf`).
- Small local models are slower and can be wrong. Always check the source file the bot names.

Tested on 27 Oct 2026 with Ollama 0.40.11, qwen2.5:3b, nomic-embed-text, ollama-python 0.6.3, chromadb 1.5.9 and pypdf 6.21.2.

🔔 Subscribe for free AI courses: https://www.youtube.com/@aditejus?sub_confirmation=1

License: MIT. Use, copy and modify freely.
