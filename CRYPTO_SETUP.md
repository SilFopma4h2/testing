# Crypto Donation Setup Instructions

## Overview
The donation system has been successfully modified to only accept cryptocurrency donations (Bitcoin and Ethereum). When donations are submitted, notifications are sent to a Discord channel via webhook.

## Required Configuration

### 1. Discord Webhook Setup
1. Create a Discord server or use an existing one
2. Go to Server Settings → Integrations → Webhooks
3. Click "New Webhook" or "Create Webhook"
4. Choose the channel where donation notifications should appear
5. Copy the webhook URL

### 2. Environment Configuration
Create a `.env` file in the project root with the following:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///ngo.db

# Mail Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@hopefoundation.org

# Discord Webhook Configuration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE
```

### 3. Update Crypto Wallet Addresses

**IMPORTANT**: Replace the placeholder wallet addresses with your actual cryptocurrency addresses.

**Current placeholder addresses to replace:**

**Bitcoin Address (in both files):**
- Current: `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`
- Replace in: `app.py` (line ~606) and `donate.html` (line ~257, 366)

**Ethereum Address (in both files):**
- Current: `0x742d35Cc6634C0532925a3b8D9f9f9f`
- Replace in: `app.py` (line ~607) and `donate.html` (line ~259, 368)

### 4. Files to Update with Your Addresses

#### app.py
```python
# Around line 605-608
crypto_addresses = {
    'bitcoin': 'YOUR_ACTUAL_BITCOIN_ADDRESS_HERE',
    'ethereum': 'YOUR_ACTUAL_ETHEREUM_ADDRESS_HERE'
}
```

#### donate.html
```html
<!-- Around line 257 and 366 -->
<small>YOUR_ACTUAL_BITCOIN_ADDRESS_HERE</small>
<small>YOUR_ACTUAL_ETHEREUM_ADDRESS_HERE</small>

<!-- In JavaScript around line 383 and 387 -->
cryptoAddress.textContent = 'YOUR_ACTUAL_BITCOIN_ADDRESS_HERE';
cryptoAddress.textContent = 'YOUR_ACTUAL_ETHEREUM_ADDRESS_HERE';
```

## Features Implemented

✅ **Crypto-Only Donations**: Only Bitcoin and Ethereum accepted
✅ **Dynamic UI**: Shows wallet address when payment method is selected
✅ **Backend Validation**: Rejects non-crypto payment methods
✅ **Discord Integration**: Rich embed notifications with donation details
✅ **Email Notifications**: Updated templates with crypto instructions
✅ **Database Storage**: All donation details saved with transaction IDs

## Discord Notification Format

When donations are submitted, Discord will receive rich embed notifications containing:
- 💰 Donation Amount
- 🪙 Cryptocurrency Type
- 🎯 Selected Project
- 👤 Donor Information (respects anonymous setting)
- 🔗 Transaction ID
- 💌 Donor Message (if provided)

## Testing

The system has been tested and verified to work correctly:
- ✅ Form validation works
- ✅ Crypto payment methods display correctly
- ✅ Non-crypto payments are rejected
- ✅ Database records created properly
- ✅ Discord webhook ready (needs URL configuration)

## Next Steps

1. Configure your Discord webhook URL in the `.env` file
2. Replace placeholder crypto addresses with your actual wallet addresses
3. Test with small donations to verify everything works correctly
4. Monitor Discord notifications to ensure proper operation

**Security Note**: Keep your `.env` file secure and never commit it to version control. The `.env.example` file is provided as a template.