# Firmware curl Reference

## 1. Authentication

### Get Signup Ticket
*(Admin only — get this from the backend admin before registering)*

### Register Account
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "YOUR_EMAIL",
    "password": "YOUR_PASSWORD",
    "full_name": "YOUR_NAME",
    "signup_ticket": "YOUR_SIGNUP_TICKET"
  }'
```

### Login (Get JWT)
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "YOUR_EMAIL",
    "password": "YOUR_PASSWORD"
  }'
```
> Returns `access_token` — use this as `YOUR_JWT` in all subsequent requests. Expires in 1800 seconds.

---

## 2. Vaults

### List Vaults (Get Vault ID)
```bash
curl http://localhost:8000/api/v1/vaults \
  -H 'Authorization: Bearer YOUR_JWT'
```
> Returns `vault_id` — needed for PIN and provisioning token endpoints.

### Create Provisioning Token
```bash
curl -X POST http://localhost:8000/api/v1/vaults/provisioning-token \
  -H 'Authorization: Bearer YOUR_JWT'
```
> Returns a provisioning token — enter this in the ESP32 captive portal form.

### Set Vault PIN
```bash
curl -X POST http://localhost:8000/api/v1/vaults/YOUR_VAULT_ID/pin \
  -H 'Authorization: Bearer YOUR_JWT' \
  -H 'Content-Type: application/json' \
  -d '{"pin": "YOUR_PIN"}'
```
> Sets the PIN for the vault. Required before PIN entry on the keypad will work.

---

## 3. Devices

### Verify PIN (Device-facing, no auth required)
```bash
curl -X POST http://localhost:8000/api/v1/devices/verify-pin \
  -H 'Content-Type: application/json' \
  -d '{
    "hardware_uuid": "YOUR_MAC_ADDRESS",
    "pin": "YOUR_PIN"
  }'
```
> Returns 200 if accepted, 401/403 if denied, 409 if PIN not set.

---

## 4. Notes

- Replace `YOUR_JWT` with the `access_token` from the login response
- Replace `YOUR_VAULT_ID` with the `vault_id` from the list vaults response
- Replace `YOUR_MAC_ADDRESS` with the ESP32 MAC address (format: `AA:BB:CC:DD:EE:FF`)
- JWT expires every 30 minutes — re-login to get a new one
- Backend runs on `http://localhost:8000` locally
- For ESP32 provisioning, use your machine's local IP instead of localhost (e.g. `http://192.168.1.9:8000`)
