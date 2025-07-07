import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import create_workflow
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build the graph
app = create_workflow() 