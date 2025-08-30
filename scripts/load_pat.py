import os
from dotenv import load_dotenv

# Load from .env first, fallback to example.
if os.path.exists('.env'):
	load_dotenv('.env')
else:
	load_dotenv('.env.example')

val = os.getenv('GITHUB_PAT')
if val:
	print('Successfully loaded the key. Ready to work.')
else:
	print('Error: Could not find the key. Add GITHUB_PAT to your .env file.')
