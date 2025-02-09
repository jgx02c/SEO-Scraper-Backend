# Simple Flask for MVP @leaps

Created by @jgx02


## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/DepositionAssistant.git
   cd DepositionAssistant
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

gunicorn -k eventlet app:app