# Google Drive API Setup Guide

This guide will walk you through setting up Google Drive API credentials to enable automatic upload of processed CSV files.

## Prerequisites

- A Google account
- Access to Google Cloud Console

## Step-by-Step Instructions

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click **"New Project"**
4. Enter a project name (e.g., "Shirt Order Automation")
5. Click **"Create"**
6. Wait for the project to be created and select it

### Step 2: Enable Google Drive API

1. In the Google Cloud Console, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Drive API"**
3. Click on **"Google Drive API"** from the results
4. Click the **"Enable"** button
5. Wait for the API to be enabled

### Step 3: Create a Service Account

1. In the Google Cloud Console, go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"Service account"**
4. Fill in the service account details:
   - **Service account name**: `shirt-order-automation` (or any name you prefer)
   - **Service account ID**: Will be auto-generated
   - **Description**: "Service account for uploading processed order files"
5. Click **"Create and Continue"**
6. Skip the optional steps (Grant access, Grant users access) and click **"Done"**

### Step 4: Create and Download Service Account Key

1. In the **"Credentials"** page, find your newly created service account
2. Click on the service account email address
3. Go to the **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Select **"JSON"** as the key type
6. Click **"Create"**
7. A JSON file will be downloaded automatically - **SAVE THIS FILE SECURELY**
   - This file contains your private credentials - never commit it to git or share it publicly
   - Recommended location: Save it in your project directory as `google-credentials.json` (but make sure it's in `.gitignore`)

### Step 5: Get Your Google Drive Folder ID

1. Open [Google Drive](https://drive.google.com/)
2. Create a new folder or navigate to an existing folder where you want to store the uploaded files
3. Click on the folder to open it
4. Look at the URL in your browser - it will look like:
   ```
   https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
   ```
5. Copy the long string after `/folders/` - this is your **Folder ID**
   - Example: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p`

### Step 6: Share Folder with Service Account

1. In Google Drive, right-click on the folder you want to use
2. Click **"Share"**
3. In the "Share" dialog, click **"Change to anyone with the link"** or add the service account email
4. **Important**: You need to share the folder with your service account email
   - Your service account email looks like: `shirt-order-automation@your-project-id.iam.gserviceaccount.com`
   - You can find this email in the Google Cloud Console under "IAM & Admin" → "Service Accounts"
5. Add the service account email and give it **"Editor"** permissions
6. Click **"Send"**

### Step 7: Configure Your Script

You have two options to configure the Google Drive credentials:

#### Option A: Environment Variables (Recommended)

Add to your `.env` file:
```bash
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
GOOGLE_CREDENTIALS_PATH=/path/to/google-credentials.json
```

#### Option B: Command-Line Arguments

When running the script:
```bash
python order_processor.py \
  --google-drive-folder-id "your_folder_id_here" \
  --google-credentials-path "/path/to/google-credentials.json"
```

### Step 8: Test the Setup

1. Make sure your `.env` file has the credentials configured (or use command-line arguments)
2. Run the order processor:
   ```bash
   python order_processor.py
   ```
3. Check the logs for a success message like:
   ```
   ✓ Successfully uploaded processed_orders_YYYYMMDD_HHMMSS.csv to Google Drive
     File ID: 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
     View at: https://drive.google.com/file/d/1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p/view
   ```
4. Verify the file appears in your Google Drive folder

## Security Best Practices

1. **Never commit credentials to git**: Make sure `google-credentials.json` is in your `.gitignore`
2. **Use environment variables**: Store sensitive information in `.env` files, not in code
3. **Limit permissions**: Only grant the service account access to the specific folder it needs
4. **Rotate keys**: Periodically regenerate service account keys for security
5. **Monitor usage**: Check Google Cloud Console regularly for any unusual API usage

## Troubleshooting

### Error: "File not found: google-credentials.json"
- **Solution**: Check that the path to your credentials file is correct
- Use absolute paths or ensure the file is in the correct relative location

### Error: "Insufficient permissions"
- **Solution**: Make sure you've shared the Google Drive folder with the service account email
- Verify the service account has "Editor" permissions on the folder

### Error: "API not enabled"
- **Solution**: Go to Google Cloud Console → APIs & Services → Library
- Search for "Google Drive API" and make sure it's enabled

### Error: "Invalid credentials"
- **Solution**: Download a new JSON key from the service account settings
- Make sure you're using the correct service account

## Additional Resources

- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [Service Account Authentication](https://cloud.google.com/iam/docs/service-accounts)
- [Google Cloud Console](https://console.cloud.google.com/)

