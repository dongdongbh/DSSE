# DSSE Forward Privacy Demo Guide

This guide will help you deliver an impressive demonstration of Dynamic Searchable Symmetric Encryption with Forward Privacy.

## Quick Start

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run the interactive demo
streamlit run app.py
```

The demo will open in your browser at `http://localhost:8501`

## Demo Script: The "Wow" Moment

Follow this script to demonstrate Forward Privacy effectively:

### Part 1: The Setup (30 seconds)

**What to say:**
> "I'm going to demonstrate Forward Privacy in searchable encryption. The key insight is that the server stores all data encrypted, and cannot link new uploads to previous searches—even if they use the same keyword."

**What to do:**
- Show the split-screen interface
- Point to LEFT side: "This is what I see as the user"
- Point to RIGHT side: "This is what the server/adversary sees"

### Part 2: First Upload (1 minute)

**What to do:**
1. On the LEFT, type keyword: `ProjectX`
2. Upload a file (any file, e.g., a PDF or image)
3. Click "Encrypt & Upload"

**What to say:**
> "Watch the right side carefully. A new entry just appeared in the server's database."

**Point to the RIGHT side:**
> "Notice this address: `a1b2c3d4...` It's completely random. The server has NO idea this file is related to 'ProjectX'. All it sees is an encrypted blob at a random location."

### Part 3: The Forward Privacy "Killer Demo" (2 minutes)

**What to do:**
1. Upload ANOTHER file with the same keyword `ProjectX`
2. Immediately point to the RIGHT side

**What to say (this is the key moment):**
> "Look! A second entry appeared: `f9e8d7c6...` Notice this address is COMPLETELY DIFFERENT from the first one. Mathematically, the server cannot tell these two uploads are related. This is Forward Privacy."

**Emphasize:**
> "Even if an attacker compromised my search for 'ProjectX' yesterday, they still cannot identify this new file I just uploaded today. Each upload uses a fresh random key that cannot be predicted."

### Part 4: Show It Works (1 minute)

**What to do:**
1. Type `ProjectX` in the search box
2. Click Search

**What to say:**
> "But I have the secret keys stored locally. Watch—when I search for 'ProjectX', I can retrieve BOTH files instantly."

**Show the results:**
> "The client can link them together using the encrypted chain, but the server cannot."

### Part 5: The Technical Explanation (optional, 2 minutes)

If your audience wants details:

**What to say:**
> "Here's how it works technically:
> 1. Each upload generates a fresh 256-bit random key
> 2. We derive a pseudorandom address using HMAC-SHA256
> 3. We encrypt the file and a pointer to the previous file in the chain
> 4. The server stores this at the random address
>
> The key insight: because keys are RANDOM (not derived from the keyword), the server cannot predict future addresses or correlate them with past searches."

## Advanced Demonstrations

### Demo 1: Multiple Keywords

Show that different keywords create isolated chains:
1. Upload files for `ProjectX`
2. Upload files for `SecretPlans`
3. Show that searches return only relevant files

### Demo 2: Scalability

Point to the server statistics:
- "This uses SQLite for persistence"
- "Can scale to millions of entries"
- "Data survives restarts"

### Demo 3: Real File Encryption

Upload actual sensitive-looking documents:
- A PDF labeled "Confidential Report"
- An image with sensitive content
- Show downloading and decrypting works

## Common Questions & Answers

**Q: What if the server gets compromised?**
> A: The server only has encrypted data. Without the client's keys (stored locally), the attacker learns nothing about keywords or file contents.

**Q: Can the server delete files?**
> A: Yes—the server is honest-but-curious. It honestly stores and retrieves data but tries to learn information. Denial-of-service attacks are outside this threat model.

**Q: What about backward privacy?**
> A: This scheme doesn't provide backward privacy. If a search is compromised, the attacker can trace back through the chain to see historical uploads. Forward privacy prevents them from identifying FUTURE uploads.

**Q: How does this compare to just using AES encryption?**
> A: Regular AES requires downloading and decrypting everything to search. This scheme allows searching within encrypted data without revealing keywords to the server.

## Visual Highlights

Point out these visual elements during the demo:

### Left Side (Client View)
- Clean, user-friendly interface
- Plain text keywords and filenames
- Fast search results

### Right Side (Server View)
- Cryptic hex strings
- Random addresses
- Encrypted blobs
- No readable information

### The Contrast
The dramatic difference between the two views is the key to demonstrating the security properties.

## Technical Talking Points

For technical audiences, mention:

1. **Cryptographic Primitives**
   - AES-256-GCM for authenticated encryption
   - HMAC-SHA256 for address derivation
   - Cryptographically secure random number generation

2. **Data Structures**
   - Chained encrypted inverted index (linked list)
   - SQLite for persistent storage
   - Binary file storage with encrypted metadata

3. **Performance**
   - Update: ~0.1-5 ms per file
   - Search: ~0.06 ms per query
   - Scales linearly with result size

4. **Security Properties**
   - Forward privacy against honest-but-curious adversary
   - IND-CPA security for file encryption
   - Authenticated encryption prevents tampering

## Troubleshooting

**Demo runs slowly:**
- Use smaller files (< 1 MB) for demo
- Clear data between runs

**Streamlit won't start:**
```bash
uv pip install --upgrade streamlit
streamlit run app.py
```

**Database locked errors:**
- Close previous demo instances
- Delete `streamlit_server.db` and restart

## Files Overview

- `app.py` - Interactive Streamlit demo (use this for presentations)
- `dsse_enhanced.py` - Full implementation with file encryption
- `dsse_forward_privacy.py` - Original implementation (for reference)

## Tips for a Great Demo

1. **Practice the script** - The "wow" moment is in the delivery
2. **Use real-looking files** - "secret_plans.pdf" is more engaging than "test.txt"
3. **Upload twice quickly** - Shows addresses are truly different
4. **Point to the screen** - Make sure audience sees the encrypted view
5. **Pause after uploads** - Let them observe the server view changing

## Customization

To customize for your audience:

```python
# In app.py, modify the title/description
st.title("Your Custom Title")

# Change color scheme in the CSS section
st.markdown("""<style>...</style>""")

# Add more metrics or visualizations as needed
```

Good luck with your demo!
