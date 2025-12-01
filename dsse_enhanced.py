"""
Dynamic Searchable Symmetric Encryption (DSSE) with Forward Privacy
Enhanced Version with Persistent Storage and File Encryption
====================================================================

Enhancements over basic version:
1. SQLite persistent storage (scales to millions of records)
2. Actual file encryption/decryption (not just document IDs)
3. Server-side file storage simulation
4. Production-ready architecture

Author: Cryptography Course Project
"""

import os
import json
import time
import secrets
import sqlite3
import shutil
from pathlib import Path
from typing import Tuple, Optional, List, Dict
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend


class CryptoHandler:
    """
    Cryptographic primitives for the DSSE scheme.

    Provides:
    - AES-GCM for authenticated encryption (both index and files)
    - HMAC-SHA256 for key derivation and address generation
    """

    @staticmethod
    def generate_random_key(length: int = 32) -> bytes:
        """Generate a cryptographically secure random key."""
        return secrets.token_bytes(length)

    @staticmethod
    def hmac_sha256(key: bytes, data: str) -> bytes:
        """Compute HMAC-SHA256 of data using key."""
        h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
        h.update(data.encode('utf-8'))
        return h.finalize()

    @staticmethod
    def derive_address(key: bytes) -> str:
        """Derive a storage address from a key using HMAC."""
        return CryptoHandler.hmac_sha256(key, "address").hex()

    @staticmethod
    def aes_gcm_encrypt(key: bytes, plaintext: bytes, nonce: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Encrypt data using AES-GCM (authenticated encryption)."""
        if nonce is None:
            nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce, ciphertext

    @staticmethod
    def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
        """Decrypt AES-GCM encrypted data."""
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def encrypt_file(file_path: str, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt an entire file using AES-GCM.

        Args:
            file_path: Path to file to encrypt
            key: 32-byte encryption key

        Returns:
            Tuple of (nonce, ciphertext, original_filename_encrypted)
        """
        # Read the file
        with open(file_path, 'rb') as f:
            plaintext = f.read()

        # Encrypt file contents
        nonce, ciphertext = CryptoHandler.aes_gcm_encrypt(key, plaintext)

        # Also encrypt the original filename for privacy
        filename = os.path.basename(file_path)
        _, filename_encrypted = CryptoHandler.aes_gcm_encrypt(key, filename.encode('utf-8'))

        return nonce, ciphertext, filename_encrypted

    @staticmethod
    def decrypt_file(nonce: bytes, ciphertext: bytes, key: bytes, output_path: str) -> str:
        """
        Decrypt a file and save to disk.

        Args:
            nonce: AES-GCM nonce
            ciphertext: Encrypted file contents
            key: 32-byte decryption key
            output_path: Where to save decrypted file

        Returns:
            Path to decrypted file
        """
        plaintext = CryptoHandler.aes_gcm_decrypt(key, nonce, ciphertext)

        with open(output_path, 'wb') as f:
            f.write(plaintext)

        return output_path


class PersistentServer:
    """
    Enhanced server with SQLite persistent storage and file storage.

    This simulates a real cloud storage provider that:
    - Stores encrypted index in SQLite (scales to millions of entries)
    - Stores encrypted files on disk
    - Provides persistence across restarts
    """

    def __init__(self, db_path: str = "server.db", storage_dir: str = "server_storage"):
        """
        Initialize persistent server.

        Args:
            db_path: Path to SQLite database
            storage_dir: Directory for storing encrypted files
        """
        self.db_path = db_path
        self.storage_dir = storage_dir

        # Create storage directory
        Path(storage_dir).mkdir(exist_ok=True)

        # Initialize SQLite database
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        # Create encrypted index table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS encrypted_index
            (address TEXT PRIMARY KEY, nonce BLOB, ciphertext BLOB)
        ''')

        # Create encrypted files table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS encrypted_files
            (file_id TEXT PRIMARY KEY,
             nonce BLOB,
             file_key BLOB,
             storage_path TEXT,
             upload_time REAL)
        ''')

        self.conn.commit()

    def store_index_node(self, address: str, nonce: bytes, ciphertext: bytes) -> None:
        """
        Store an encrypted index node.

        Args:
            address: Pseudorandom lookup address
            nonce: AES-GCM nonce
            ciphertext: Encrypted node data
        """
        self.cursor.execute(
            "INSERT OR REPLACE INTO encrypted_index VALUES (?, ?, ?)",
            (address, nonce, ciphertext)
        )
        self.conn.commit()

    def get_index_node(self, address: str) -> Optional[Tuple[bytes, bytes]]:
        """
        Retrieve an encrypted index node.

        Args:
            address: Lookup address

        Returns:
            Tuple of (nonce, ciphertext) or None if not found
        """
        self.cursor.execute(
            "SELECT nonce, ciphertext FROM encrypted_index WHERE address=?",
            (address,)
        )
        result = self.cursor.fetchone()
        return result if result else None

    def store_encrypted_file(self, file_id: str, nonce: bytes, file_key: bytes,
                            encrypted_data: bytes) -> str:
        """
        Store an encrypted file on disk.

        Args:
            file_id: Unique identifier for the file
            nonce: AES-GCM nonce used for encryption
            file_key: Key used to encrypt the file
            encrypted_data: The encrypted file contents

        Returns:
            Storage path where file was saved
        """
        # Generate storage path
        storage_path = os.path.join(self.storage_dir, f"{file_id}.enc")

        # Write encrypted file to disk
        with open(storage_path, 'wb') as f:
            f.write(encrypted_data)

        # Store metadata in database
        self.cursor.execute(
            "INSERT OR REPLACE INTO encrypted_files VALUES (?, ?, ?, ?, ?)",
            (file_id, nonce, file_key, storage_path, time.time())
        )
        self.conn.commit()

        return storage_path

    def get_encrypted_file(self, file_id: str) -> Optional[Tuple[bytes, bytes, bytes]]:
        """
        Retrieve an encrypted file.

        Args:
            file_id: File identifier

        Returns:
            Tuple of (nonce, file_key, encrypted_data) or None
        """
        # Get metadata from database
        self.cursor.execute(
            "SELECT nonce, file_key, storage_path FROM encrypted_files WHERE file_id=?",
            (file_id,)
        )
        result = self.cursor.fetchone()

        if not result:
            return None

        nonce, file_key, storage_path = result

        # Read encrypted file from disk
        try:
            with open(storage_path, 'rb') as f:
                encrypted_data = f.read()
            return (nonce, file_key, encrypted_data)
        except FileNotFoundError:
            return None

    def search(self, start_key: bytes, start_address: str) -> List[Dict]:
        """
        Traverse the encrypted chain to retrieve all document information.

        Args:
            start_key: Key for the head of the chain
            start_address: Address of the head node

        Returns:
            List of document info dictionaries
        """
        results = []
        current_key = start_key
        current_address = start_address

        while True:
            # Retrieve encrypted node
            node = self.get_index_node(current_address)

            if node is None:
                break

            nonce, ciphertext = node

            # Decrypt the node
            try:
                plaintext = CryptoHandler.aes_gcm_decrypt(current_key, nonce, ciphertext)
                node_data = json.loads(plaintext.decode('utf-8'))

                # Extract document info
                results.append({
                    'file_id': node_data['file_id'],
                    'original_name': node_data.get('original_name', 'unknown'),
                    'file_key': node_data['file_key']
                })

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
                print(f"Error decrypting node: {e}")
                break

        return results

    def get_stats(self) -> Dict:
        """Get storage statistics."""
        self.cursor.execute("SELECT COUNT(*) FROM encrypted_index")
        index_count = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM encrypted_files")
        file_count = self.cursor.fetchone()[0]

        # Calculate storage size
        db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

        storage_size = 0
        if os.path.exists(self.storage_dir):
            for f in Path(self.storage_dir).glob("*.enc"):
                storage_size += f.stat().st_size

        return {
            'index_entries': index_count,
            'encrypted_files': file_count,
            'db_size_bytes': db_size,
            'storage_size_bytes': storage_size,
            'total_size_bytes': db_size + storage_size
        }

    def clear_all(self) -> None:
        """Clear all data (for testing)."""
        self.cursor.execute("DELETE FROM encrypted_index")
        self.cursor.execute("DELETE FROM encrypted_files")
        self.conn.commit()

        # Remove all encrypted files
        if os.path.exists(self.storage_dir):
            shutil.rmtree(self.storage_dir)
            Path(self.storage_dir).mkdir(exist_ok=True)


class EnhancedClient:
    """
    Enhanced client with file encryption capabilities.

    Supports:
    - Encrypting and uploading actual files
    - Maintaining encrypted index with forward privacy
    - Downloading and decrypting files
    """

    def __init__(self, state_file: str = "client_state.json"):
        """
        Initialize enhanced client.

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

    def upload_file(self, server: PersistentServer, keyword: str,
                    file_path: str) -> Tuple[str, float]:
        """
        Encrypt and upload a file with forward privacy.

        Complete Pipeline:
        1. Generate random file encryption key
        2. Encrypt the file contents
        3. Upload encrypted file to server storage
        4. Update encrypted index (forward privacy chain)

        Args:
            server: Server instance
            keyword: Keyword to associate with file
            file_path: Path to file to encrypt and upload

        Returns:
            Tuple of (file_id, elapsed_time)
        """
        start_time = time.time()

        # Generate unique file ID and encryption key
        file_id = secrets.token_hex(16)
        file_key = CryptoHandler.generate_random_key(32)

        # Encrypt the file
        nonce, ciphertext, _ = CryptoHandler.encrypt_file(file_path, file_key)

        # Upload encrypted file to server
        server.store_encrypted_file(file_id, nonce, file_key, ciphertext)

        # Now update the encrypted index (forward privacy)
        # Retrieve old chain head (if keyword exists)
        old_key_hex = None
        old_address = None
        if keyword in self.state:
            old_key_hex, old_address = self.state[keyword]

        # FORWARD PRIVACY: Generate fresh random key for index node
        new_key = CryptoHandler.generate_random_key(32)
        new_address = CryptoHandler.derive_address(new_key)

        # Create index node
        node_data = {
            'file_id': file_id,
            'original_name': os.path.basename(file_path),
            'file_key': file_key.hex(),
            'old_key': old_key_hex,
            'old_address': old_address
        }

        # Encrypt the index node
        plaintext = json.dumps(node_data).encode('utf-8')
        nonce, ciphertext = CryptoHandler.aes_gcm_encrypt(new_key, plaintext)

        # Store encrypted index node
        server.store_index_node(new_address, nonce, ciphertext)

        # Update local state
        self.state[keyword] = (new_key.hex(), new_address)
        self._save_state()

        end_time = time.time()
        return file_id, end_time - start_time

    def search_files(self, server: PersistentServer,
                     keyword: str) -> Tuple[Optional[List[Dict]], float]:
        """
        Search for all files associated with a keyword.

        Args:
            server: Server instance
            keyword: Keyword to search for

        Returns:
            Tuple of (file_info_list, elapsed_time)
        """
        start_time = time.time()

        if keyword not in self.state:
            end_time = time.time()
            return None, end_time - start_time

        # Get current chain head
        current_key_hex, current_address = self.state[keyword]
        current_key = bytes.fromhex(current_key_hex)

        # Issue search token to server
        results = server.search(current_key, current_address)

        end_time = time.time()
        return results, end_time - start_time

    def download_file(self, server: PersistentServer, file_id: str,
                      file_key: str, output_path: str) -> bool:
        """
        Download and decrypt a file.

        Args:
            server: Server instance
            file_id: ID of file to download
            file_key: Hex-encoded decryption key
            output_path: Where to save decrypted file

        Returns:
            True if successful, False otherwise
        """
        # Retrieve encrypted file
        file_data = server.get_encrypted_file(file_id)

        if file_data is None:
            return False

        nonce, stored_key, encrypted_data = file_data

        # Decrypt and save
        key_bytes = bytes.fromhex(file_key)
        CryptoHandler.decrypt_file(nonce, encrypted_data, key_bytes, output_path)

        return True

    def clear_state(self) -> None:
        """Clear all local state."""
        self.state = {}
        if os.path.exists(self.state_file):
            os.remove(self.state_file)


def demo_enhanced_system():
    """
    Demonstrate the enhanced DSSE system with file encryption.
    """
    print("\n" + "=" * 80)
    print("Enhanced DSSE with Persistent Storage and File Encryption")
    print("=" * 80 + "\n")

    # Initialize
    server = PersistentServer("demo_server.db", "demo_storage")
    client = EnhancedClient("demo_client_state.json")

    # Clear previous data
    server.clear_all()
    client.clear_state()

    print("DEMONSTRATION: File Encryption Pipeline")
    print("-" * 80 + "\n")

    # Create some test files
    test_files_dir = "test_files"
    Path(test_files_dir).mkdir(exist_ok=True)

    # Create test documents
    test_files = [
        ("secret_plans.txt", "This document contains secret project plans."),
        ("financial_report.txt", "Q4 2024 Financial Report - Confidential"),
        ("meeting_notes.txt", "Meeting notes from strategy session."),
    ]

    for filename, content in test_files:
        with open(os.path.join(test_files_dir, filename), 'w') as f:
            f.write(content)

    # Upload files
    print("Phase 1: Encrypting and Uploading Files")
    print("-" * 40)

    uploads = [
        ("confidential", os.path.join(test_files_dir, "secret_plans.txt")),
        ("confidential", os.path.join(test_files_dir, "financial_report.txt")),
        ("meetings", os.path.join(test_files_dir, "meeting_notes.txt")),
    ]

    for keyword, file_path in uploads:
        file_id, elapsed = client.upload_file(server, keyword, file_path)
        print(f"  ✓ Uploaded '{os.path.basename(file_path)}'")
        print(f"    Keyword: {keyword}")
        print(f"    File ID: {file_id}")
        print(f"    Time: {elapsed*1000:.2f} ms\n")

    # Show server stats
    stats = server.get_stats()
    print("\nServer Storage Statistics:")
    print(f"  Index entries: {stats['index_entries']}")
    print(f"  Encrypted files: {stats['encrypted_files']}")
    print(f"  Database size: {stats['db_size_bytes']:,} bytes")
    print(f"  File storage: {stats['storage_size_bytes']:,} bytes")
    print(f"  Total: {stats['total_size_bytes']:,} bytes")

    # Search and download
    print("\n" + "-" * 80)
    print("Phase 2: Searching and Downloading Files")
    print("-" * 40)

    keyword = "confidential"
    results, elapsed = client.search_files(server, keyword)

    print(f"\nSearch for '{keyword}': {elapsed*1000:.2f} ms")

    if results:
        print(f"Found {len(results)} files:\n")

        # Create download directory
        download_dir = "downloads"
        Path(download_dir).mkdir(exist_ok=True)

        for i, file_info in enumerate(results, 1):
            print(f"  {i}. {file_info['original_name']}")
            print(f"     File ID: {file_info['file_id']}")

            # Download and decrypt
            output_path = os.path.join(download_dir, file_info['original_name'])
            success = client.download_file(
                server,
                file_info['file_id'],
                file_info['file_key'],
                output_path
            )

            if success:
                print(f"     ✓ Downloaded to: {output_path}")
                # Show decrypted content
                with open(output_path, 'r') as f:
                    content = f.read()
                print(f"     Content preview: {content[:50]}...")
            print()

    # Demonstrate forward privacy
    print("\n" + "=" * 80)
    print("FORWARD PRIVACY DEMONSTRATION")
    print("=" * 80)
    print("""
Observe what happened:

1. TWO files were uploaded with keyword "confidential"
2. Each upload created a DIFFERENT random address in the server index
3. The server CANNOT link these two uploads without the client's keys
4. Even if an adversary observes a search for "confidential", they cannot
   predict or identify future uploads for the same keyword

This is Forward Privacy in action!
""")

    # Cleanup
    print("\nCleaning up demo files...")
    shutil.rmtree(test_files_dir, ignore_errors=True)
    shutil.rmtree(download_dir, ignore_errors=True)
    server.clear_all()
    client.clear_state()

    print("Demo completed!\n")


if __name__ == "__main__":
    demo_enhanced_system()
