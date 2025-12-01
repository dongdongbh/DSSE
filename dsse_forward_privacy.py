"""
Dynamic Searchable Symmetric Encryption (DSSE) with Forward Privacy
====================================================================

This implementation uses a "Chained Encrypted Inverted Index" approach to achieve
Forward Privacy, ensuring that the server cannot link new updates to previous searches.

Key Security Properties:
- Forward Privacy: New updates use fresh random keys, making it impossible for the
  server to link them to previous search queries or updates.
- Honest-but-Curious Server: The server correctly executes operations but may try
  to learn information from stored data.
- Encrypted Chain: Each keyword's document list is stored as a linked list where
  each node is encrypted with a unique random key.

Author: Cryptography Course Project
"""

import os
import json
import time
import secrets
from typing import Tuple, Optional, List, Dict
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend


class CryptoHandler:
    """
    Cryptographic primitives for the DSSE scheme.

    Provides:
    - AES-GCM for authenticated encryption
    - HMAC-SHA256 for key derivation and address generation
    """

    @staticmethod
    def generate_random_key(length: int = 32) -> bytes:
        """
        Generate a cryptographically secure random key.

        This is crucial for Forward Privacy - each update uses a fresh
        random key that cannot be predicted or linked to previous keys.

        Args:
            length: Key length in bytes (default 32 for AES-256)

        Returns:
            Random key bytes
        """
        return secrets.token_bytes(length)

    @staticmethod
    def hmac_sha256(key: bytes, data: str) -> bytes:
        """
        Compute HMAC-SHA256 of data using key.

        Used to derive deterministic addresses from keys while maintaining
        one-way properties (cannot reverse engineer key from address).

        Args:
            key: Secret key for HMAC
            data: String data to hash

        Returns:
            32-byte HMAC digest
        """
        h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
        h.update(data.encode('utf-8'))
        return h.finalize()

    @staticmethod
    def derive_address(key: bytes) -> str:
        """
        Derive a storage address from a key using HMAC.

        This creates a pseudorandom address that the server uses as a lookup key.
        The address reveals no information about the key or keyword.

        Args:
            key: The secret key

        Returns:
            Hex-encoded address string
        """
        return CryptoHandler.hmac_sha256(key, "address").hex()

    @staticmethod
    def aes_gcm_encrypt(key: bytes, plaintext: bytes, nonce: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-GCM (authenticated encryption).

        AES-GCM provides both confidentiality and authenticity, preventing
        the server from tampering with encrypted nodes.

        Args:
            key: 32-byte encryption key
            plaintext: Data to encrypt
            nonce: Optional 12-byte nonce (generated if not provided)

        Returns:
            Tuple of (nonce, ciphertext_with_tag)
        """
        if nonce is None:
            nonce = os.urandom(12)  # 96-bit nonce for AES-GCM

        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce, ciphertext

    @staticmethod
    def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
        """
        Decrypt AES-GCM encrypted data.

        Args:
            key: 32-byte decryption key
            nonce: 12-byte nonce used during encryption
            ciphertext: Encrypted data with authentication tag

        Returns:
            Decrypted plaintext bytes

        Raises:
            InvalidTag: If ciphertext has been tampered with
        """
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)


class Server:
    """
    Honest-but-curious server that stores the encrypted index.

    The server:
    - Stores encrypted nodes at pseudorandom addresses
    - Performs search by traversing the encrypted chain
    - Cannot learn which keyword is being searched (forward privacy)
    - Cannot link new updates to old searches (fresh random keys)
    """

    def __init__(self):
        """Initialize empty encrypted index storage."""
        # Dictionary mapping address -> (nonce, ciphertext)
        self.encrypted_index: Dict[str, Tuple[bytes, bytes]] = {}

    def store(self, address: str, nonce: bytes, ciphertext: bytes) -> None:
        """
        Store an encrypted node at the given address.

        Args:
            address: Pseudorandom lookup address
            nonce: AES-GCM nonce
            ciphertext: Encrypted node data
        """
        self.encrypted_index[address] = (nonce, ciphertext)

    def search(self, start_key: bytes, start_address: str) -> List[str]:
        """
        Traverse the encrypted chain to retrieve all document IDs.

        This implements the search protocol:
        1. Decrypt node at start_address using start_key
        2. Extract document ID and pointer to previous node
        3. Recursively follow the chain until reaching the end

        Forward Privacy: The server learns which chain is being traversed,
        but cannot link this to previous searches or predict future updates
        because each key is random and independent.

        Args:
            start_key: Key for the head of the chain
            start_address: Address of the head node

        Returns:
            List of document IDs for the keyword (in reverse chronological order)
        """
        results = []
        current_key = start_key
        current_address = start_address

        # Traverse the chain backwards
        while current_address in self.encrypted_index:
            # Retrieve encrypted node
            nonce, ciphertext = self.encrypted_index[current_address]

            # Decrypt the node
            try:
                plaintext = CryptoHandler.aes_gcm_decrypt(current_key, nonce, ciphertext)
                node_data = json.loads(plaintext.decode('utf-8'))

                # Extract document ID
                doc_id = node_data['doc_id']
                results.append(doc_id)

                # Get pointer to previous node
                old_key_hex = node_data.get('old_key')
                old_address = node_data.get('old_address')

                # Check if this is the end of the chain
                if old_key_hex is None or old_address is None:
                    break

                # Move to previous node
                current_key = bytes.fromhex(old_key_hex)
                current_address = old_address

            except Exception as e:
                # Decryption failed or malformed data
                print(f"Error decrypting node: {e}")
                break

        return results

    def get_storage_size(self) -> int:
        """
        Get the number of encrypted nodes stored.

        Returns:
            Number of entries in the index
        """
        return len(self.encrypted_index)

    def get_storage_bytes(self) -> int:
        """
        Calculate total storage size in bytes.

        Returns:
            Total bytes used by the encrypted index
        """
        total = 0
        for address, (nonce, ciphertext) in self.encrypted_index.items():
            total += len(address.encode('utf-8'))
            total += len(nonce)
            total += len(ciphertext)
        return total


class Client:
    """
    Client managing the DSSE scheme with forward privacy.

    The client:
    - Maintains local state mapping keywords to chain heads
    - Generates fresh random keys for each update (Forward Privacy)
    - Creates encrypted nodes forming a linked list per keyword
    - Issues search tokens to the server

    Forward Privacy Guarantee:
    Each update uses a fresh random key, making it computationally impossible
    for the server to link new updates to previous searches. The server cannot
    predict future addresses or correlate updates across time.
    """

    def __init__(self, state_file: str = "client_state.json"):
        """
        Initialize client with state storage.

        Args:
            state_file: Path to persistent state file
        """
        self.state_file = state_file
        # State: { keyword -> (current_key_hex, current_address) }
        self.state: Dict[str, Tuple[str, str]] = {}
        self._load_state()

    def _load_state(self) -> None:
        """Load client state from disk if it exists."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                self.state = json.load(f)

    def _save_state(self) -> None:
        """Persist client state to disk."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def update(self, server: Server, keyword: str, doc_id: str) -> float:
        """
        Add a document ID to a keyword's encrypted chain.

        Forward Privacy Implementation:
        1. Generate a fresh random key (unpredictable by server)
        2. Derive new address from this key (unlinkable to previous addresses)
        3. Encrypt node containing doc_id and pointer to old chain head
        4. Update local state to point to new head

        The server sees:
        - A new random address (cannot predict or link to keyword)
        - Encrypted data (cannot read without key)
        - No correlation between updates of the same keyword

        Args:
            server: Server instance to store encrypted node
            keyword: Keyword to associate with document
            doc_id: Document identifier to add

        Returns:
            Time taken for the update operation (seconds)
        """
        start_time = time.time()

        # Retrieve old chain head (if keyword exists)
        old_key_hex = None
        old_address = None
        if keyword in self.state:
            old_key_hex, old_address = self.state[keyword]

        # FORWARD PRIVACY: Generate fresh random key
        # This is NOT derived from the keyword or previous keys
        # The server cannot predict this key or link it to previous updates
        new_key = CryptoHandler.generate_random_key(32)

        # Derive new address from the random key
        new_address = CryptoHandler.derive_address(new_key)

        # Create node: (doc_id, pointer to previous node)
        node_data = {
            'doc_id': doc_id,
            'old_key': old_key_hex,
            'old_address': old_address
        }

        # Encrypt the node with the new random key
        plaintext = json.dumps(node_data).encode('utf-8')
        nonce, ciphertext = CryptoHandler.aes_gcm_encrypt(new_key, plaintext)

        # Send encrypted node to server
        server.store(new_address, nonce, ciphertext)

        # Update local state: keyword now points to new head
        self.state[keyword] = (new_key.hex(), new_address)
        self._save_state()

        end_time = time.time()
        return end_time - start_time

    def search(self, server: Server, keyword: str) -> Tuple[Optional[List[str]], float]:
        """
        Search for all documents associated with a keyword.

        Search Protocol:
        1. Look up current chain head from local state
        2. Send search token (key, address) to server
        3. Server traverses the encrypted chain
        4. Server returns list of document IDs

        Privacy Note: The server learns that a search is happening and which
        chain is traversed, but cannot link this to future updates due to
        forward privacy (future keys are random and unpredictable).

        Args:
            server: Server instance holding encrypted index
            keyword: Keyword to search for

        Returns:
            Tuple of (document_id_list, search_time_seconds)
            Returns (None, time) if keyword not found
        """
        start_time = time.time()

        # Check if keyword exists in local state
        if keyword not in self.state:
            end_time = time.time()
            return None, end_time - start_time

        # Get current chain head
        current_key_hex, current_address = self.state[keyword]
        current_key = bytes.fromhex(current_key_hex)

        # Issue search token to server (key + address)
        results = server.search(current_key, current_address)

        end_time = time.time()
        return results, end_time - start_time

    def clear_state(self) -> None:
        """Clear all local state (for testing purposes)."""
        self.state = {}
        if os.path.exists(self.state_file):
            os.remove(self.state_file)


class Benchmark:
    """
    Evaluation framework for measuring DSSE performance.

    Metrics:
    - Update Latency: Time to add a document to a keyword
    - Search Latency: Time to retrieve all documents for a keyword
    - Storage Size: Number of nodes and total bytes stored
    """

    @staticmethod
    def generate_dummy_data(num_keywords: int, num_docs: int) -> Dict[str, List[str]]:
        """
        Generate synthetic dataset for benchmarking.

        Args:
            num_keywords: Number of unique keywords
            num_docs: Total number of documents

        Returns:
            Dictionary mapping keywords to document ID lists
        """
        import random

        data = {}
        keywords = [f"keyword_{i}" for i in range(num_keywords)]

        # Distribute documents across keywords (some overlap)
        for doc_id in range(num_docs):
            # Each document gets 1-3 random keywords
            num_kw = random.randint(1, 3)
            selected_keywords = random.sample(keywords, num_kw)

            for kw in selected_keywords:
                if kw not in data:
                    data[kw] = []
                data[kw].append(f"doc_{doc_id}")

        return data

    @staticmethod
    def run_benchmark(num_keywords: int = 100, num_docs: int = 1000):
        """
        Run comprehensive performance evaluation.

        Args:
            num_keywords: Number of keywords to test
            num_docs: Number of documents to index
        """
        print("=" * 80)
        print("DSSE Forward Privacy Benchmark")
        print("=" * 80)
        print(f"Configuration: {num_keywords} keywords, {num_docs} documents\n")

        # Initialize
        server = Server()
        client = Client("benchmark_state.json")
        client.clear_state()

        # Generate data
        print("Generating dummy data...")
        data = Benchmark.generate_dummy_data(num_keywords, num_docs)

        # Measure update performance
        print("\n" + "-" * 80)
        print("PHASE 1: UPDATE OPERATIONS")
        print("-" * 80)

        update_times = []
        update_count = 0

        print("Adding documents to encrypted index...")
        for keyword, doc_ids in data.items():
            for doc_id in doc_ids:
                elapsed = client.update(server, keyword, doc_id)
                update_times.append(elapsed)
                update_count += 1

                if update_count % 100 == 0:
                    print(f"  Progress: {update_count} updates completed")

        avg_update_time = sum(update_times) / len(update_times) * 1000  # Convert to ms
        print(f"\nTotal updates: {update_count}")
        print(f"Average update time: {avg_update_time:.4f} ms")
        print(f"Total update time: {sum(update_times):.2f} seconds")

        # Measure storage
        print("\n" + "-" * 80)
        print("STORAGE METRICS")
        print("-" * 80)

        storage_entries = server.get_storage_size()
        storage_bytes = server.get_storage_bytes()

        print(f"Total encrypted nodes: {storage_entries}")
        print(f"Total storage size: {storage_bytes:,} bytes ({storage_bytes / 1024:.2f} KB)")
        print(f"Average node size: {storage_bytes / storage_entries:.2f} bytes")

        # Measure search performance
        print("\n" + "-" * 80)
        print("PHASE 2: SEARCH OPERATIONS")
        print("-" * 80)

        search_times = []
        result_sizes = []

        print("Searching for all keywords...")
        for i, keyword in enumerate(data.keys()):
            results, elapsed = client.search(server, keyword)
            search_times.append(elapsed)
            result_sizes.append(len(results) if results else 0)

            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1} searches completed")

        avg_search_time = sum(search_times) / len(search_times) * 1000  # Convert to ms
        avg_result_size = sum(result_sizes) / len(result_sizes)

        print(f"\nTotal searches: {len(search_times)}")
        print(f"Average search time: {avg_search_time:.4f} ms")
        print(f"Average results per keyword: {avg_result_size:.2f} documents")

        # Analyze search time by result size
        print("\n" + "-" * 80)
        print("SEARCH TIME BY RESULT SIZE")
        print("-" * 80)

        # Group by result size ranges
        size_ranges = [(1, 5), (6, 10), (11, 20), (21, 50), (51, 100)]

        for min_size, max_size in size_ranges:
            filtered_times = [
                search_times[i] * 1000 for i, size in enumerate(result_sizes)
                if min_size <= size <= max_size
            ]

            if filtered_times:
                avg_time = sum(filtered_times) / len(filtered_times)
                print(f"  {min_size:3d}-{max_size:3d} results: {avg_time:8.4f} ms (n={len(filtered_times)})")

        # Forward privacy explanation
        print("\n" + "=" * 80)
        print("FORWARD PRIVACY GUARANTEE")
        print("=" * 80)
        print("""
This DSSE scheme achieves Forward Privacy through the following mechanisms:

1. RANDOM KEY GENERATION
   - Each update generates a fresh random 256-bit key
   - Keys are NOT derived from keywords, previous keys, or any predictable source
   - Server cannot predict future keys even if it compromises past keys

2. UNLINKABLE ADDRESSES
   - Storage addresses are derived via HMAC(random_key, "address")
   - Each address appears pseudorandom to the server
   - Server cannot link addresses to keywords or correlate updates

3. ENCRYPTED CHAIN STRUCTURE
   - Each node is encrypted with its unique random key
   - Node contains: (doc_id, previous_key, previous_address)
   - Server learns chain traversal during search but cannot predict future nodes

4. SECURITY AGAINST ADVERSARY
   - Passive adversary: Cannot learn anything from observing updates
   - Active adversary (post-search): Cannot link future updates to past searches
   - File injection: New files use new random keys, unlinkable to existing data

RESULT: The server cannot correlate new updates with previous searches or
        predict future updates, even after observing search patterns.
""")

        # Cleanup
        client.clear_state()

        print("=" * 80)
        print("Benchmark completed successfully!")
        print("=" * 80)


def main():
    """
    Main demonstration of the DSSE scheme.
    """
    print("\n" + "=" * 80)
    print("Dynamic Searchable Symmetric Encryption with Forward Privacy")
    print("=" * 80 + "\n")

    # Quick demonstration
    print("DEMONSTRATION: Basic Operations")
    print("-" * 80 + "\n")

    # Initialize
    server = Server()
    client = Client("demo_state.json")
    client.clear_state()

    # Add some documents
    print("Adding documents:")
    keywords_docs = [
        ("cryptography", "paper_001.pdf"),
        ("cryptography", "paper_002.pdf"),
        ("encryption", "paper_001.pdf"),
        ("encryption", "paper_003.pdf"),
        ("cryptography", "paper_004.pdf"),
    ]

    for keyword, doc_id in keywords_docs:
        elapsed = client.update(server, keyword, doc_id)
        print(f"  Added '{doc_id}' to keyword '{keyword}' ({elapsed*1000:.2f} ms)")

    print(f"\nServer storage: {server.get_storage_size()} encrypted nodes")

    # Search
    print("\nSearching:")
    for keyword in ["cryptography", "encryption", "nonexistent"]:
        results, elapsed = client.search(server, keyword)
        if results:
            print(f"  '{keyword}': {results} ({elapsed*1000:.2f} ms)")
        else:
            print(f"  '{keyword}': Not found ({elapsed*1000:.2f} ms)")

    # Cleanup
    client.clear_state()

    # Run full benchmark
    print("\n" + "=" * 80)
    print("Running Full Benchmark...")
    print("=" * 80 + "\n")

    Benchmark.run_benchmark(num_keywords=100, num_docs=1000)


if __name__ == "__main__":
    main()
