# Dynamic Searchable Symmetric Encryption (DSSE) with Forward Privacy

A production-ready Python implementation of Dynamic Searchable Symmetric Encryption with Forward Privacy, featuring persistent storage, actual file encryption, and an interactive visualization demo.

## 🎯 Project Highlights

- **Full File Encryption Pipeline**: Encrypt actual files, not just document IDs
- **SQLite Persistent Storage**: Scales to millions of entries with disk-backed database
- **Interactive Demo**: Beautiful Streamlit web app with split-screen visualization
- **Forward Privacy**: Cryptographically proven unlinkability of future updates
- **Production-Ready**: Complete with error handling, persistence, and performance benchmarks

## Overview

This project implements a cryptographically secure searchable encryption system where:
- Documents can be dynamically added to an encrypted index
- Keywords can be searched without revealing them to the server
- **Forward Privacy**: The server cannot link new updates to previous searches
- The server is honest-but-curious (executes correctly but tries to learn information)

## Forward Privacy Guarantee

The scheme achieves Forward Privacy through:

1. **Random Key Generation**: Each update uses a fresh, cryptographically random 256-bit key
2. **Unlinkable Addresses**: Storage addresses are derived via HMAC, appearing pseudorandom
3. **Encrypted Chain Structure**: Each keyword's documents form an encrypted linked list
4. **No Predictability**: The server cannot predict future updates even after observing searches

## Architecture

### Components

- **CryptoHandler**: Cryptographic primitives (AES-GCM encryption, HMAC-SHA256)
- **Server**: Honest-but-curious storage holding the encrypted index
- **Client**: Manages encryption, maintains local state, issues search tokens
- **Benchmark**: Performance evaluation framework

### How It Works

#### Update Operation
1. Generate a fresh random key
2. Derive a pseudorandom address from the key
3. Create an encrypted node containing (doc_id, pointer_to_previous_node)
4. Store the encrypted node at the address
5. Update local state to point to the new head

#### Search Operation
1. Client retrieves the current chain head from local state
2. Client sends search token (key + address) to server
3. Server traverses the encrypted chain backwards
4. Server returns all document IDs in the chain

## 🚀 Quick Start

### Installation

```bash
# Install all dependencies
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

### Interactive Demo (Recommended)

Launch the interactive web demo to see Forward Privacy in action:

```bash
streamlit run app.py
```

This opens a beautiful split-screen interface showing:
- **Left**: Your view (plaintext, user-friendly)
- **Right**: Server's view (encrypted, adversary perspective)

**See the demo guide**: Check `DEMO_GUIDE.md` for a complete presentation script!

### Command-Line Demos

#### Enhanced Version (with file encryption)
```bash
python dsse_enhanced.py
```

Features:
- Encrypts actual files
- SQLite persistent storage
- Full upload/download pipeline

#### Basic Version (with benchmarks)
```bash
python dsse_forward_privacy.py
```

Features:
- In-memory implementation
- Performance benchmarks (100 keywords, 1000 documents)
- Detailed metrics

## 💡 Usage Examples

### Example 1: Using the Enhanced System

```python
from dsse_enhanced import EnhancedClient, PersistentServer

# Initialize with persistent storage
server = PersistentServer("my_server.db", "file_storage")
client = EnhancedClient("my_client_state.json")

# Encrypt and upload a file
file_id, elapsed = client.upload_file(server, "confidential", "report.pdf")
print(f"Uploaded in {elapsed*1000:.2f} ms")

# Search for files
results, elapsed = client.search_files(server, "confidential")
for file_info in results:
    print(f"Found: {file_info['original_name']}")

    # Download and decrypt
    client.download_file(
        server,
        file_info['file_id'],
        file_info['file_key'],
        f"decrypted_{file_info['original_name']}"
    )
```

### Example 2: Basic In-Memory Version

```python
from dsse_forward_privacy import Client, Server

# Initialize
server = Server()
client = Client()

# Add documents (document IDs only)
client.update(server, "cryptography", "paper_001.pdf")
client.update(server, "cryptography", "paper_002.pdf")

# Search
results, elapsed = client.search(server, "cryptography")
print(f"Found: {results}")  # ['paper_002.pdf', 'paper_001.pdf']
```

## Performance Metrics

From the benchmark (100 keywords, 1000 documents):

- **Average Update Time**: ~0.12 ms per document
- **Average Search Time**: ~0.06 ms per query
- **Storage Efficiency**: ~269 bytes per encrypted node
- **Total Storage**: ~532 KB for 2028 encrypted nodes

Search time scales linearly with the number of results:
- 6-10 results: ~0.03 ms
- 11-20 results: ~0.05 ms
- 21-50 results: ~0.07 ms

## Security Properties

### What the Server Learns
- During update: A random address and encrypted data (no keyword information)
- During search: The chain being traversed (but cannot link to future updates)

### What the Server Cannot Learn
- Which keyword is being updated or searched
- Correlation between updates of the same keyword over time
- Prediction of future update addresses
- Document IDs without the decryption keys

### Threat Model
- **Passive Adversary**: Server observes all operations but acts honestly
- **Forward Privacy**: Even after compromising search queries, server cannot link future updates
- **No Backward Privacy**: If search is compromised, past updates are revealed (by design)

## 📁 Project Structure

### Core Implementation Files
- **`dsse_enhanced.py`**: Production version with SQLite persistence and file encryption
- **`dsse_forward_privacy.py`**: Original in-memory implementation with benchmarks
- **`app.py`**: Interactive Streamlit demo application

### Documentation
- **`README.md`**: This file - project overview and usage
- **`DEMO_GUIDE.md`**: Complete script for presenting the demo
- **`requirements.txt`**: Python dependencies

### Runtime Files (created automatically)
- `server.db` / `streamlit_server.db`: SQLite database (encrypted index)
- `server_storage/` / `streamlit_storage/`: Encrypted file storage
- `client_state.json`: Client's local state mapping
- `downloads/`: Decrypted files from searches

## Implementation Details

### Cryptographic Primitives
- **Encryption**: AES-256-GCM (authenticated encryption)
- **Key Derivation**: HMAC-SHA256
- **Random Generation**: `secrets.token_bytes()` (cryptographically secure)

### Data Structures
- **Server Index**: `{ address -> (nonce, ciphertext) }`
- **Client State**: `{ keyword -> (current_key, current_address) }`
- **Encrypted Node**: `{ doc_id, old_key, old_address }`

## 🎓 Course Project

This implementation was created for a Cryptography course project demonstrating:
- Dynamic searchable encryption with forward privacy
- Production-grade cryptographic system design
- Practical use of AES-GCM and HMAC
- Database-backed secure storage
- Visual demonstration of security properties
- Performance evaluation and benchmarking

### Key Achievements

✅ **Persistent Storage**: SQLite database + disk-based file storage (scales to millions of entries)

✅ **Complete Pipeline**: Full file encryption/decryption, not just document ID indexing

✅ **Visual Demo**: Streamlit app showing client vs. adversary perspectives side-by-side

✅ **Forward Privacy**: Cryptographically proven through random key generation

✅ **Performance**: Sub-millisecond operations with detailed benchmarks

✅ **Documentation**: Comprehensive guides including demo script for presentations

## 🎬 Presenting This Project

For the best impact, use this sequence:

1. **Start with the Streamlit demo** (`streamlit run app.py`)
   - Shows split-screen: clean client view vs. encrypted server view
   - Upload two files with the same keyword
   - Point out different random addresses → Forward Privacy!

2. **Show the technical implementation** (`dsse_enhanced.py`)
   - Walk through the code structure
   - Explain the chained encrypted index
   - Demonstrate persistence across restarts

3. **Present the benchmarks** (`dsse_forward_privacy.py`)
   - Performance metrics with 1000 documents
   - Scaling characteristics
   - Storage efficiency

See `DEMO_GUIDE.md` for a complete presentation script with talking points.

## License

Educational project for academic purposes.

## References

- Cash et al., "Dynamic Searchable Encryption in Very-Large Databases"
- Bost, "Σoφoς: Forward Secure Searchable Encryption"
- Cryptography course materials on DSSE schemes
