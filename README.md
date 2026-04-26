# MIFAREkit

> [!NOTE]
> This has only been tested with FM11RF08 Chinese Card which is seemingly a clone of Mifare Classic

## Why did I make this?
I was having trouble finding resources on smart cards and had access to a couple of chinese cards (FM11RF08) which is a Mifareclass clone. So I made a UI so that I can easily read and write to cards. The card I have does not have exposed chip (IC) but has NFC.

## How To Start

Clone the repo
```bash
git clone https://github.com/raahimfareed/mifarekit.git
cd mifarekit
```

Create a virtual environment
```bash
python -m venv .venv
```

Activate the virtual environment
```bash
# On Windows Powershell
.\.venv\Scripts\Activate.ps1

# On POSIX
source ./.venv/bin/activate
```

Install dependencies
```bash
pip install -r requirements.txt
```

Run the dev server
```bash
# This starts the server @ localhost:8000
python manage.py runserver
```