# ToneBridge Outlook Add-in

## Overview
The ToneBridge Outlook add-in brings powerful email transformation capabilities directly into Microsoft Outlook, allowing users to:
- Transform email tone (soften, clarify, structure)
- Analyze email priority and clarity
- Apply AI-powered improvements
- Access all features through a convenient task pane

## Features

### Compose Mode
- **Quick Actions**: One-click transformations (Soften, Clarify, Summarize, Structure)
- **Tone Adjustment**: Fine-tune transformation intensity (0-3 levels)
- **Advanced Options**: 
  - Preserve formatting
  - Include signature
  - Target audience selection
- **Real-time Preview**: See transformed content before applying

### Analyze Mode
- **Email Metrics**: Tone, clarity score, priority level, suggested response time
- **Eisenhower Matrix**: Visual priority classification
- **Improvement Suggestions**: AI-powered recommendations

### Quick Commands
- **Soften Button**: Instantly make emails warmer and more considerate
- **Clarify Button**: Improve structure and clarity with one click

## Installation

### Prerequisites
- Microsoft Outlook 2016 or later (Windows/Mac)
- Outlook on the web
- Office 365 subscription (recommended)

### Development Setup

1. **Host the add-in files**:
   ```bash
   # Navigate to the outlook directory
   cd integrations/outlook
   
   # Start a local server (using Python)
   python3 -m http.server 3000
   
   # Or using Node.js
   npx http-server -p 3000
   ```

2. **Update manifest URLs**:
   - Edit `manifest.xml` to point to your development server
   - Replace `https://tonebridge.io` with `http://localhost:3000`

3. **Sideload the add-in**:

   **For Outlook on Windows:**
   - Open Outlook
   - Go to File > Manage Add-ins
   - Click "Upload My Add-in"
   - Browse to and select `manifest.xml`

   **For Outlook on Mac:**
   - Open Outlook
   - Go to Tools > Add-ins
   - Click the "+" button and select "Add from file"
   - Browse to and select `manifest.xml`

   **For Outlook on the web:**
   - Open Outlook on the web
   - Click the Settings gear icon
   - Select "View all Outlook settings"
   - Go to Mail > Customize actions
   - Click "Install add-in" and upload `manifest.xml`

### Production Deployment

1. **Host static files**:
   ```bash
   # Upload these files to your web server:
   - taskpane.html
   - taskpane.css
   - taskpane.js
   - commands.html
   - icon-16.png
   - icon-32.png
   - icon-64.png
   - icon-80.png
   ```

2. **Update manifest.xml**:
   - Replace all `localhost` URLs with your production domain
   - Update icon URLs to point to hosted images

3. **Submit to AppSource** (optional):
   - Create a Microsoft Partner Center account
   - Submit the add-in for certification
   - Follow Microsoft's validation guidelines

## Configuration

### API Endpoints
Edit `taskpane.js` and `commands.html` to configure API endpoints:

```javascript
const API_BASE_URL = 'https://api.tonebridge.io/api/v1';
const LOCAL_API_URL = 'http://localhost:8080/api/v1';
```

### Authentication
Implement proper authentication in the `getAuthToken()` function:

```javascript
async function getAuthToken() {
    return await Office.auth.getAccessToken({ 
        forceConsent: false 
    });
}
```

### Icons
Create and host the following icon sizes:
- `icon-16.png` - 16x16 pixels
- `icon-32.png` - 32x32 pixels  
- `icon-64.png` - 64x64 pixels
- `icon-80.png` - 80x80 pixels

## Usage

### Transform Email
1. Open a new email or reply
2. Click the "Transform" button in the ribbon
3. Select transformation options in the task pane
4. Click "Transform Email"
5. Review the result and click "Apply to Email"

### Quick Actions
1. While composing an email, click "Soften" or "Clarify" in the ribbon
2. The transformation is applied automatically

### Analyze Email
1. Open any email
2. Click the "Analyze" button in the ribbon
3. Switch to "Analyze" mode in the task pane
4. Click "Analyze Current Email"
5. Review metrics and suggestions

## API Integration

### Transform Endpoint
```http
POST /api/v1/transform
Content-Type: application/json
Authorization: Bearer {token}

{
  "text": "Email content...",
  "transformation_type": "soften",
  "intensity": 2,
  "options": {
    "preserve_formatting": true,
    "include_signature": true,
    "target_audience": "executive"
  }
}
```

### Analyze Endpoint
```http
POST /api/v1/analyze
Content-Type: application/json
Authorization: Bearer {token}

{
  "text": "Email content..."
}
```

## Troubleshooting

### Add-in not loading
- Ensure manifest.xml is valid (use Office Add-in Validator)
- Check that all URLs in manifest are accessible
- Clear Office cache and reload

### API connection issues
- Verify API endpoints are correct
- Check authentication token is valid
- Ensure CORS is configured for your domain

### Permission errors
- Grant necessary permissions when prompted
- Ensure ReadWriteItem permission is set in manifest

## Security Considerations

1. **Authentication**: Always use OAuth 2.0 or Office SSO
2. **Data Protection**: Encrypt sensitive data in transit
3. **Input Validation**: Sanitize all user inputs
4. **Rate Limiting**: Implement API rate limits
5. **Error Handling**: Never expose sensitive info in errors

## Development Tips

### Debugging
```javascript
// Enable verbose logging
console.log('Debug:', data);

// Use Office.context.mailbox.item.notificationMessages
item.notificationMessages.addAsync('debug', {
    type: 'informationalMessage',
    message: 'Debug info here'
});
```

### Testing
- Use Outlook Web App for quick iteration
- Test on multiple Outlook versions
- Verify mobile compatibility

## Support

For issues or questions:
- GitHub Issues: [ToneBridge/issues](https://github.com/tonebridge/issues)
- Documentation: [docs.tonebridge.io](https://docs.tonebridge.io)
- Email: support@tonebridge.io

## License

Copyright (c) 2025 ToneBridge. All rights reserved.