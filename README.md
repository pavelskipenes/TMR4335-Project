# TMR4335 Propulsion systems, Safety and Environment

## Installation
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
python position.py
```
various plots are now available in `plots/`.

## Accessing data from Kystverket
create an account at [Kystdatahuset](https://kystdatahuset.no/)
```bash
cp .env.example .env
# update credentials in .env
dotenv run bash kystdatahuset_bearer.sh | jq '.data.JWT' > bearer.txt
```
use `bearer.txt` as authentication in [Kystdatahuset Swagger REST API documentation](https://kystdatahuset.no/ws/swagger/index.html)


