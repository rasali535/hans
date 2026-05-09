
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
        print("IMPORT SUCCESS")
        
        # Mock image
        mock_image = "iVBORw0KGgoAAAANSUvE4NdnhvW70FcaX"
        
        print("RUNNING PIPELINE...")
        try:
            # We'll use a very short timeout for the HTTP calls in agents.py if we can
            # But run_pipeline uses AMD_TIMEOUT from env.
            result = await agents.run_pipeline(mock_image, notes="Test", product_spec="Test")
            print("PIPELINE RESULT GENERATED")
            print(json.dumps(result, indent=2)[:500])
        except Exception as e:
            print(f"PIPELINE FAILED: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"IMPORT FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline())
