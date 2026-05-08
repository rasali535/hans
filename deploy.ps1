# Deploy ForgeSight to Hugging Face Spaces
# Run this from the project root: c:\Users\user\OneDrive\Desktop\hans\hans

# 1. Clone the HF Space repo (if not already done)
git clone https://huggingface.co/spaces/rasAli02/ForgeSight hf_space_repo

# 2. Copy all deployment files into the cloned repo
Copy-Item hf_space\* hf_space_repo\ -Force

# 3. Push to HF Spaces
Set-Location hf_space_repo
git add -A
git commit -m "Deploy ForgeSight Gradio backend with AMD MI300X agent pipeline"
git push

# After push, the space will build and start at:
# https://rasali02-forgesight.hf.space
