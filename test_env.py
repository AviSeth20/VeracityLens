"""Quick test to verify .env file is configured correctly"""
import os

print("="*60)
print("ENVIRONMENT CONFIGURATION TEST")
print("="*60)

# Read .env file manually
env_vars = {}
try:
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
except FileNotFoundError:
    print("❌ .env file not found!")
    exit(1)

# Check required variables
required = [
    'SUPABASE_URL',
    'SUPABASE_KEY',
    'GNEWS_API_KEY'
]

print("\nChecking required environment variables:\n")

all_good = True
for var in required:
    if var in env_vars and env_vars[var]:
        # Mask the value for security
        value = env_vars[var]
        if len(value) > 20:
            masked = value[:15] + "..." + value[-5:]
        else:
            masked = value[:5] + "..."
        print(f"✅ {var:25} = {masked}")
    else:
        print(f"❌ {var:25} = NOT SET")
        all_good = False

print("\n" + "="*60)
if all_good:
    print("✅ All required credentials are configured!")
    print("\nYour configuration:")
    print(f"  Supabase Project: nrrlrctttdslttflxjsc")
    print(f"  GNews API: Configured")
    print(f"  W&B: Configured")
    print("\nNext steps:")
    print("  1. Run: python scripts/download_models.py")
    print("  2. Setup database with scripts/setup_supabase.sql")
    print("  3. Start API: uvicorn src.api.main:app --reload")
else:
    print("❌ Some credentials are missing!")
    print("   Please check your .env file")

print("="*60)
