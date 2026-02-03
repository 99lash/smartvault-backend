# ONE TIME SETUP
```bash
wsl --install
sudo apt update
sudo apt install -y make
```
Step 1. Install Docker Desktop
- Open Docker Desktop
- Make sure it’s running (not stopped)
Step 2. Enable WSL integration
Docker Desktop → Settings → Resources → WSL Integration
- Turn ON: Enable integration with my default WSL distro
- Also turn ON your distro (looks like Sharkie or similar)
- Click Apply & Restart
Step 3. Back in WSL, verify Docker works
```bash
docker version
docker compose version
```
Step 4. Create a folder inside WSL:
```bash
mkdir -p ~/projects
```
Step 5: Copy your repo into it
```bash
cp -r /mnt/d/SmartVault/api ~/projects/smartvault-api # /mnt/<drive letter>/<your folder where SMRTVLT API is located>/<project root directory>
```
Step 6: Go there
```bash
cd ~/projects/smartvault-api
```
Step 7. Run your workflow again
```bash
make dev
```

