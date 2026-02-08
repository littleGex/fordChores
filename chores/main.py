import sys
import os
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
from chores import create_app

app = create_app()

if __name__ == "__main__":
    # Use 0.0.0.0 for Docker and a port from environment if needed
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
