"""
Streamlit Demo App for DSSE with Forward Privacy
=================================================

This creates a "split-screen" visualization showing:
- LEFT: Client view (plaintext, user-friendly)
- RIGHT: Server view (encrypted, adversary perspective)

The goal is to visually demonstrate Forward Privacy by showing how
the server sees only random addresses and encrypted data.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
import time as time_module

from dsse_enhanced import EnhancedClient, PersistentServer, CryptoHandler


# Configure page
st.set_page_config(
    layout="wide",
    page_title="DSSE Forward Privacy Demo",
    page_icon="🔐"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stAlert {
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'server' not in st.session_state:
    st.session_state.server = PersistentServer("streamlit_server.db", "streamlit_storage")
    st.session_state.client = EnhancedClient("streamlit_client_state.json")
    st.session_state.upload_history = []
    st.session_state.search_history = []

# Title
st.title("🔐 DSSE with Forward Privacy: Interactive Demo")

st.markdown("""
This demo visualizes **Forward Privacy** in searchable encryption. Watch how the server
sees only random addresses and encrypted data, while the client can perform meaningful searches.
""")

# Add explanation
with st.expander("ℹ️ What is Forward Privacy?", expanded=False):
    st.markdown("""
    **Forward Privacy** ensures that even if an adversary observes your searches,
    they cannot link future updates to those searches.

    **Key Property:** Each file upload generates a fresh random key, making the
    server's view completely unlinkable across time.

    **Why it matters:** If an attacker compromises your search query today,
    they still cannot identify files you add tomorrow for the same keyword.
    """)

# Create two columns
col1, col2 = st.columns([1, 1])

# =============================================================================
# LEFT COLUMN: CLIENT VIEW (Trusted/Plaintext)
# =============================================================================
with col1:
    st.header("👤 Client View (You)")
    st.markdown("*Trusted environment - you see plaintext*")

    # File Upload Section
    st.subheader("📤 Upload Encrypted File")

    with st.form("upload_form", clear_on_submit=True):
        keyword_input = st.text_input(
            "Keyword/Tag",
            placeholder="e.g., 'ProjectX', 'confidential', 'Q4-reports'",
            help="A keyword to associate with this file"
        )

        uploaded_file = st.file_uploader(
            "Choose a file",
            help="Any file type supported"
        )

        submit_upload = st.form_submit_button("🔒 Encrypt & Upload", use_container_width=True)

        if submit_upload and keyword_input and uploaded_file:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name

            try:
                # Encrypt and upload
                start = time_module.time()
                file_id, elapsed = st.session_state.client.upload_file(
                    st.session_state.server,
                    keyword_input,
                    tmp_path
                )

                # Record in history
                st.session_state.upload_history.append({
                    'keyword': keyword_input,
                    'filename': uploaded_file.name,
                    'file_id': file_id,
                    'time': elapsed * 1000
                })

                st.success(f"✅ Uploaded '{uploaded_file.name}' under keyword '{keyword_input}'")
                st.info(f"⏱️ Upload time: {elapsed*1000:.2f} ms")

                # Clean up
                os.unlink(tmp_path)

                # Force refresh
                st.rerun()

            except Exception as e:
                st.error(f"❌ Upload failed: {str(e)}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    st.divider()

    # Search Section
    st.subheader("🔍 Search Files")

    with st.form("search_form"):
        search_keyword = st.text_input(
            "Search by keyword",
            placeholder="Enter keyword to search"
        )

        submit_search = st.form_submit_button("🔎 Search", use_container_width=True)

        if submit_search and search_keyword:
            results, elapsed = st.session_state.client.search_files(
                st.session_state.server,
                search_keyword
            )

            st.session_state.search_history.append({
                'keyword': search_keyword,
                'count': len(results) if results else 0,
                'time': elapsed * 1000
            })

            # Store results in session state for display outside form
            st.session_state.last_search_results = results
            st.session_state.last_search_time = elapsed
            st.session_state.last_search_keyword = search_keyword

    # Display search results outside the form
    if 'last_search_results' in st.session_state and st.session_state.last_search_results is not None:
        results = st.session_state.last_search_results
        elapsed = st.session_state.last_search_time
        search_keyword = st.session_state.last_search_keyword

        if results:
            st.success(f"✅ Found {len(results)} file(s) in {elapsed*1000:.2f} ms")

            # Display results
            st.markdown("#### 📁 Results:")

            for i, file_info in enumerate(results, 1):
                with st.container():
                    col_a, col_b = st.columns([3, 1])

                    with col_a:
                        st.markdown(f"**{i}. {file_info['original_name']}**")
                        st.caption(f"File ID: `{file_info['file_id'][:16]}...`")

                    with col_b:
                        # Download button (outside form)
                        if st.button(f"⬇️ Download", key=f"download_{file_info['file_id']}"):
                            # Create downloads directory
                            download_dir = "downloads"
                            Path(download_dir).mkdir(exist_ok=True)

                            output_path = os.path.join(
                                download_dir,
                                file_info['original_name']
                            )

                            success = st.session_state.client.download_file(
                                st.session_state.server,
                                file_info['file_id'],
                                file_info['file_key'],
                                output_path
                            )

                            if success:
                                st.success(f"✅ Downloaded to `{output_path}`")
                            else:
                                st.error("❌ Download failed")

        else:
            st.warning(f"⚠️ No files found for keyword '{search_keyword}'")

    # Upload History
    if st.session_state.upload_history:
        st.divider()
        st.subheader("📋 Recent Uploads")

        history_df = pd.DataFrame(st.session_state.upload_history[-5:])  # Last 5
        history_df = history_df[['keyword', 'filename', 'time']]
        history_df['time'] = history_df['time'].apply(lambda x: f"{x:.2f} ms")
        history_df.columns = ['Keyword', 'Filename', 'Upload Time']

        st.dataframe(history_df, use_container_width=True, hide_index=True)

# =============================================================================
# RIGHT COLUMN: SERVER VIEW (Adversary/Encrypted)
# =============================================================================
with col2:
    st.header("☁️ Server View (Adversary)")
    st.markdown("*Honest-but-curious server - sees only encrypted data*")

    # Server statistics
    stats = st.session_state.server.get_stats()

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.metric("Index Entries", stats['index_entries'])

    with col_b:
        st.metric("Encrypted Files", stats['encrypted_files'])

    with col_c:
        total_mb = stats['total_size_bytes'] / (1024 * 1024)
        st.metric("Storage", f"{total_mb:.2f} MB")

    st.divider()

    # Encrypted Index View
    st.subheader("🗂️ Encrypted Index")
    st.caption("What the server stores (addresses and encrypted nodes)")

    # Query the database to show encrypted index
    cursor = st.session_state.server.cursor
    cursor.execute("SELECT address, nonce, ciphertext FROM encrypted_index ORDER BY rowid DESC LIMIT 10")
    index_rows = cursor.fetchall()

    if index_rows:
        display_data = []
        for address, nonce, ciphertext in index_rows:
            display_data.append({
                'Address': address[:16] + "..." + address[-8:],
                'Nonce': nonce.hex()[:16] + "...",
                'Encrypted Data': ciphertext.hex()[:24] + "...",
                'Size': f"{len(ciphertext)} bytes"
            })

        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.info("🔒 The server sees only random addresses and encrypted data. It cannot determine which keyword each entry belongs to.")
    else:
        st.info("📭 Index is empty. Upload a file to see encrypted entries appear here.")

    st.divider()

    # Encrypted Files View
    st.subheader("💾 Encrypted File Storage")
    st.caption("Files stored on disk (encrypted)")

    cursor.execute("SELECT file_id, nonce, storage_path FROM encrypted_files ORDER BY upload_time DESC LIMIT 5")
    file_rows = cursor.fetchall()

    if file_rows:
        file_display = []
        for file_id, nonce, storage_path in file_rows:
            file_size = os.path.getsize(storage_path) if os.path.exists(storage_path) else 0
            file_display.append({
                'File ID': file_id[:16] + "...",
                'Nonce': nonce.hex()[:16] + "...",
                'Size': f"{file_size:,} bytes"
            })

        df_files = pd.DataFrame(file_display)
        st.dataframe(df_files, use_container_width=True, hide_index=True)

        st.info("🔐 Files are encrypted with unique keys. The server cannot read the contents or even know the original filenames.")
    else:
        st.info("📭 No encrypted files stored yet.")

# =============================================================================
# Bottom Section: Forward Privacy Explanation
# =============================================================================
st.divider()

st.header("🎯 Forward Privacy Demonstration")

col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    st.markdown("""
    ### How to See Forward Privacy in Action

    1. **Upload two files** with the same keyword (e.g., "secret")
    2. **Watch the Server View** (right column)
    3. **Notice:** Two completely different addresses appear
    4. **Key Insight:** The server cannot link these two entries together

    Even if an adversary observes you searching for "secret", they cannot
    identify future uploads for the same keyword because each uses a fresh
    random key.
    """)

with col_exp2:
    st.markdown("""
    ### Security Guarantees

    ✅ **Forward Privacy**: Future updates are unlinkable to past searches

    ✅ **Encrypted Storage**: All files and index entries are encrypted

    ✅ **Persistent**: Data survives restarts (SQLite + disk storage)

    ✅ **Scalable**: Can handle millions of entries

    ⚠️ **No Backward Privacy**: If a search is compromised, past entries
    can be traced back through the chain (by design).
    """)

# Clear button
st.divider()

col_clear1, col_clear2, col_clear3 = st.columns([1, 1, 1])

with col_clear2:
    if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
        st.session_state.server.clear_all()
        st.session_state.client.clear_state()
        st.session_state.upload_history = []
        st.session_state.search_history = []
        st.success("✅ All data cleared!")
        st.rerun()

# Footer
st.divider()
st.caption("🎓 Cryptography Course Project | DSSE with Forward Privacy")
