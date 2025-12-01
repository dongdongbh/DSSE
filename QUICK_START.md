# Quick Start Guide

## Installation (30 seconds)

```bash
cd /home/dd/Documents/courses/628-crypto/project/code
uv pip install -r requirements.txt
```

## Run the Interactive Demo (NOW!)

```bash
streamlit run app.py
```

Opens at: http://localhost:8501

## What You'll See

### Split Screen Layout

```
┌─────────────────────────────┬─────────────────────────────┐
│  👤 CLIENT VIEW             │  ☁️ SERVER VIEW             │
│  (What you see)             │  (What the adversary sees)  │
├─────────────────────────────┼─────────────────────────────┤
│  • Upload files             │  • Random addresses         │
│  • Search keywords          │  • Encrypted blobs          │
│  • See plaintext results    │  • No readable information  │
└─────────────────────────────┴─────────────────────────────┘
```

## 5-Minute Demo Flow

### Step 1: Upload First File (1 min)
1. Enter keyword: `ProjectX`
2. Upload any file (PDF, image, text)
3. Click "Encrypt & Upload"
4. **Watch RIGHT side** → New encrypted entry appears with random address

### Step 2: Upload Second File - THE KEY MOMENT (2 min)
1. Enter SAME keyword: `ProjectX`
2. Upload another file
3. Click "Encrypt & Upload"
4. **Watch RIGHT side** → A DIFFERENT random address appears
5. **Point this out**: "The server cannot link these two entries!"

### Step 3: Search and Verify (1 min)
1. Search for: `ProjectX`
2. See BOTH files returned
3. **Explain**: "Only I can link them because I have the secret keys"

### Step 4: Explain Forward Privacy (1 min)
> "Even if an attacker observed my search for 'ProjectX' yesterday,
> they cannot identify this new file I just uploaded today because
> each upload uses a fresh random key that's impossible to predict."

## Alternative Demos

### Command-Line Demo (File Encryption)
```bash
python dsse_enhanced.py
```

Shows:
- Actual file encryption/decryption
- SQLite persistence
- Upload/download pipeline

### Benchmark Demo (Performance)
```bash
python dsse_forward_privacy.py
```

Shows:
- Performance with 1000 documents
- Timing metrics
- Scalability analysis

## Troubleshooting

**Port already in use:**
```bash
streamlit run app.py --server.port 8502
```

**Database locked:**
```bash
rm streamlit_server.db
streamlit run app.py
```

**Module not found:**
```bash
uv pip install --upgrade -r requirements.txt
```

## Tips for Best Impact

1. **Use the Streamlit demo** - Visual impact is crucial
2. **Upload twice quickly** - Shows addresses are truly different
3. **Point to the screen** - Direct attention to the encrypted view
4. **Pause after each upload** - Let the audience absorb what changed
5. **Use descriptive keywords** - "SecretPlans" is better than "test"

## Next Steps

After the demo, show the code:
1. Open `dsse_enhanced.py` - Show the implementation
2. Explain the chained encrypted index structure
3. Walk through the `upload_file()` method
4. Point out the random key generation (Line ~285)

## Full Documentation

- `README.md` - Complete project documentation
- `DEMO_GUIDE.md` - Detailed presentation script
- `dsse_enhanced.py` - Source code with comments

Good luck!
