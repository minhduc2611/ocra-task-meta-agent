# Password Reset Feature Setup

This document explains how to set up and use the password reset feature with PrivateEmail SMTP.

## Environment Variables

The following environment variables need to be configured for the password reset feature to work:

### Required Variables

```bash
# PrivateEmail SMTP Configuration
SMTP_USERNAME=your-email@yourdomain.com  # Your PrivateEmail address
SMTP_PASSWORD=your_email_password        # Your PrivateEmail password

# Optional SMTP Configuration (defaults provided)
SMTP_SERVER=mail.privateemail.com        # Default PrivateEmail SMTP server
SMTP_PORT=587                           # Default port (587 for TLS)
FROM_EMAIL=your-email@yourdomain.com    # From email (defaults to SMTP_USERNAME)
DOMAIN_URL=http://localhost:3000        # Your application URL
```

### PrivateEmail SMTP Settings

According to [PrivateEmail's documentation](https://privateemail.com/), the standard SMTP settings are:
- **SMTP Server:** `mail.privateemail.com`
- **Port:** `587` (TLS) or `465` (SSL)
- **Authentication:** Username and Password
- **Security:** TLS/STARTTLS

## API Endpoints

### 1. Request Password Reset

**Endpoint:** `POST /api/v1/request-password-reset`

**Request Body:**
```json
{
  "email": "user@yourdomain.com"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "If this email is registered, you will receive a reset link"
}
```

**Features:**
- Generates a secure reset token that expires in 1 hour
- Sends a beautifully formatted email with a magic link
- For security, always returns success regardless of whether the email exists

### 2. Reset Password

**Endpoint:** `POST /api/v1/reset-password`

**Request Body:**
```json
{
  "token": "secure_reset_token_from_email",
  "new_password": "new_secure_password"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Password has been successfully reset"
}
```

**Features:**
- Validates the reset token and checks expiration
- Updates the user's password with bcrypt hashing
- Marks the token as used to prevent reuse
- Sends a confirmation email
- Enforces minimum password length (6 characters)

## Email Templates

The feature includes professional HTML email templates:

### Password Reset Email
- Clean, responsive design
- Prominent reset button
- Fallback text link for accessibility
- Clear expiration notice (1 hour)
- Security messaging

### Confirmation Email
- Confirms successful password reset
- Security alert if user didn't make the change
- Link to login page

## Security Features

1. **Token Security:**
   - Uses cryptographically secure random tokens
   - 32-byte URL-safe tokens
   - 1-hour expiration time
   - One-time use (marked as used after reset)

2. **Privacy Protection:**
   - Doesn't reveal whether email exists in system
   - Secure token generation
   - Hashed password storage

3. **SMTP Security:**
   - TLS encryption for all email transmission
   - Secure authentication with PrivateEmail
   - Professional email delivery

4. **Error Handling:**
   - Proper error messages without revealing sensitive information
   - Comprehensive logging for debugging
   - Graceful fallbacks for email delivery issues

## Database Schema

The feature automatically creates a `PasswordResetTokens` collection in Weaviate with:

- `email`: User's email address
- `token`: Secure reset token
- `expires_at`: Token expiration timestamp
- `created_at`: Token creation timestamp
- `used`: Boolean flag to prevent reuse

## Quick Setup Guide

### Step 1: Configure PrivateEmail Account
1. Ensure you have an active PrivateEmail account
2. Note your email address and password
3. Verify SMTP access is enabled (it should be by default)

### Step 2: Set Environment Variables
```bash
export SMTP_USERNAME="your-email@yourdomain.com"
export SMTP_PASSWORD="your_email_password"
export FROM_EMAIL="your-email@yourdomain.com"  # Optional
export DOMAIN_URL="http://localhost:3000"     # Optional
```

### Step 3: Test SMTP Connection
You can test your SMTP connection with this simple Python script:
```python
import smtplib
import ssl
import os

def test_smtp():
    smtp_server = "mail.privateemail.com"
    smtp_port = 587
    username = os.getenv('SMTP_USERNAME')
    password = os.getenv('SMTP_PASSWORD')
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(username, password)
            print("✅ SMTP connection successful!")
            return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

test_smtp()
```

## Testing

You can test the endpoints using curl:

```bash
# Request password reset
curl -X POST http://localhost:5000/api/v1/request-password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "test@yourdomain.com"}'

# Reset password (use token from email)
curl -X POST http://localhost:5000/api/v1/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token": "your_token_here", "new_password": "newpassword123"}'
```

## Dependencies

No additional dependencies required! The feature uses Python's built-in libraries:
- `smtplib` - for SMTP email sending
- `ssl` - for secure connections
- `email.mime` - for email formatting

## Alternative SMTP Settings

If the default settings don't work, you may need to check with PrivateEmail support for your specific SMTP settings. Some variations might include:

### Common PrivateEmail SMTP Configurations:
```bash
# Standard configuration
SMTP_SERVER=mail.privateemail.com
SMTP_PORT=587  # TLS

# Alternative configuration (SSL)
SMTP_SERVER=mail.privateemail.com
SMTP_PORT=465  # SSL

# If you have a custom domain
SMTP_SERVER=mail.yourdomain.com  # Check with PrivateEmail
SMTP_PORT=587
```

## Frontend Integration

On your frontend, you'll need:

1. **Password Reset Request Page:**
   - Form with email input
   - Calls `/api/v1/request-password-reset`
   - Shows success message

2. **Password Reset Page:**
   - Extracts token from URL query parameter
   - Form with new password input
   - Calls `/api/v1/reset-password`
   - Redirects to login on success

Example URL structure:
- Reset request: `http://localhost:3000/forgot-password`
- Reset form: `http://localhost:3000/reset-password?token=abc123...`

## Troubleshooting

### Common Issues:

1. **"Email service not configured" error:**
   - Check that `SMTP_USERNAME` and `SMTP_PASSWORD` are set
   - Verify credentials are correct

2. **SMTP Authentication Failed:**
   - Double-check your PrivateEmail username and password
   - Ensure your PrivateEmail account is active
   - Check if two-factor authentication is enabled

3. **Connection Timeout:**
   - Verify SMTP server: `mail.privateemail.com`
   - Try port 465 (SSL) instead of 587 (TLS)
   - Check firewall settings

4. **Emails not being delivered:**
   - Check spam/junk folder
   - Verify FROM_EMAIL is set to your PrivateEmail address
   - Ensure recipient email is valid

5. **SSL/TLS Errors:**
   - Try changing port from 587 to 465
   - Check if your network blocks SMTP ports

### Testing SMTP Settings:
```python
# Test with different ports
def test_smtp_ports():
    servers = [
        ("mail.privateemail.com", 587, "TLS"),
        ("mail.privateemail.com", 465, "SSL"),
    ]
    
    for server, port, method in servers:
        print(f"Testing {server}:{port} ({method})")
        # Test connection logic here
```

### Get Support:
- **PrivateEmail Support:** Available 24/7 according to their website
- **SMTP Documentation:** Check your PrivateEmail control panel for specific settings
- **Application Logs:** Monitor your application logs for detailed error messages

### Monitoring:
- Monitor application logs for SMTP errors
- Check email delivery in your PrivateEmail control panel
- Use try-catch blocks to handle SMTP exceptions gracefully 