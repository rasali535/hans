# Deploy ForgeSight to Hugging Face Spaces
# Run this from the project root: c:\Users\user\OneDrive\Desktop\hans\hans

# 1. Clone/Update the HF Space repo
if (!(Test-Path hf_space_repo)) {
    git clone https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/ForgeSight hf_space_repo
}

# 2. Copy all deployment files recursively into the cloned repo
Copy-Item -Path "hf_space\*" -Destination "hf_space_repo\" -Recurse -Force

# 3. Push to HF Spaces
Set-Location hf_space_repo
git add -A
git commit -m "🚀 ForgeSight: Enhanced AMD MI300X connectivity with Smart Discovery"
git push

# After push, the space will build and start at:
# https://rasali02-forgesight.hf.space
