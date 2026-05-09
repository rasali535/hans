
import asyncio
import base64
import json
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath("backend"))

async def test_pipeline():
    try:
        import agents
        print("✅ agents.py imported successfully")
        
        # Mock image (small transparent pixel)
        mock_image = "iVBORw0KGgoAAAANSUvE4NdnhvW70FcaX" # dummy data
        
        print("Running pipeline...")
        # We'll use a small timeout to see if it even starts
        try:
            result = await agents.run_pipeline(mock_image, notes="Testing pipeline", product_spec="Concrete")
            print("✅ Pipeline result generated")
            print(json.dumps(result, indent=2)[:500] + "...")
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline())
