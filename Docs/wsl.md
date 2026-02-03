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
Step 4. Run your workflow again
```bash
cd /mnt/d/SmartVault/api # /mnt/<drive letter>/<your folder where SMRTVLT API is located>/<project root directory>
make dev
```

