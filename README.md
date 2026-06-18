# Myanmar Address Parser with Groq AI

A Telegram bot + Python pipeline that:
1. Accepts CSV files via Telegram
2. Parses Myanmar addresses using Groq AI (Llama 3.3 70B)
3. Structures addresses according to MIMU standards
4. Sends results back to Telegram in batches

## Setup

```bash
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
export TELEGRAM_TOKEN="your_bot_token"
export GROQ_API_KEY="your_groq_key"

python get_csv.py    # Upload CSV via Telegram
python script.py     # Process addresses
```
