import sys
import os

# This adds the parent directory (/app) to the Python path
# so that 'from chores import create_app' works correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chores import create_app 

app = create_app()

if __name__ == "__main__":
    # Use 0.0.0.0 for Docker and a port from environment if needed
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
