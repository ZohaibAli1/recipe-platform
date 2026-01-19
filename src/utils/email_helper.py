import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Email configuration - MUST be set via environment variables
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', '')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))


def send_password_reset_email(user_email, username, reset_token, base_url='http://localhost:5000'):
    """Send password reset email to user"""
    try:
        # Create reset URL
        reset_url = f"{base_url}/?reset_token={reset_token}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'CulinaryVerse - Password Reset Request'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = user_email
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .header {{
                    background: linear-gradient(135deg, #2c3e50, #34495e);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #ff6b35, #e55a2b);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #6c757d;
                }}
                .warning {{
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 10px;
                    border-radius: 4px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍳 CulinaryVerse</h1>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>We received a request to reset your password. Click the button below to reset your password:</p>
                    
                    <center>
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </center>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #007bff;">{reset_url}</p>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong>
                        <ul>
                            <li>This link will expire in <strong>1 hour</strong></li>
                            <li>If you didn't request this, please ignore this email</li>
                            <li>Never share this link with anyone</li>
                        </ul>
                    </div>
                    
                    <p>Thank you,<br>The CulinaryVerse Team</p>
                </div>
                <div class="footer">
                    <p>© 2024 CulinaryVerse. All rights reserved.</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text content (fallback)
        text_content = f"""
        CulinaryVerse - Password Reset Request
        
        Hello {username},
        
        We received a request to reset your password.
        Click the link below or copy and paste it into your browser:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Thank you,
        The CulinaryVerse Team
        """
        
        # Attach both parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_admin_notification(admin_email, username, user_email, reset_time):
    """Send notification to admin about password reset"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'CulinaryVerse - Password Reset Notification'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = admin_email
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .header {{
                    background: linear-gradient(135deg, #2c3e50, #34495e);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .info-box {{
                    background: #e7f3ff;
                    border: 1px solid #3498db;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 15px 0;
                }}
                .info-row {{
                    margin: 8px 0;
                }}
                .label {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Admin Notification</h1>
                </div>
                <div class="content">
                    <h2>Password Reset Request</h2>
                    <p>A user has requested a password reset:</p>
                    
                    <div class="info-box">
                        <div class="info-row">
                            <span class="label">Username:</span> {username}
                        </div>
                        <div class="info-row">
                            <span class="label">Email:</span> {user_email}
                        </div>
                        <div class="info-row">
                            <span class="label">Request Time:</span> {reset_time}
                        </div>
                    </div>
                    
                    <p>This is an automated notification for admin records.</p>
                    
                    <p>Best regards,<br>CulinaryVerse System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text content
        text_content = f"""
        CulinaryVerse - Password Reset Notification
        
        A user has requested a password reset:
        
        Username: {username}
        Email: {user_email}
        Request Time: {reset_time}
        
        This is an automated notification for admin records.
        """
        
        # Attach both parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending admin notification: {e}")
        return False


def send_rating_notification(author_email, author_name, recipe_title, rating_value, reviewer_name):
    try:
        stars = '★' * rating_value + '☆' * (5 - rating_value)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'CulinaryVerse - New Rating on "{recipe_title}"'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = author_email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .header {{
                    background: linear-gradient(135deg, #2c3e50, #34495e);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .rating-box {{
                    background: linear-gradient(135deg, #fff3cd, #ffeeba);
                    border: 1px solid #ffc107;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: center;
                }}
                .stars {{
                    font-size: 32px;
                    color: #ff6b35;
                    letter-spacing: 5px;
                }}
                .recipe-title {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin: 10px 0;
                }}
                .reviewer {{
                    color: #6c757d;
                    font-style: italic;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍳 New Rating!</h1>
                </div>
                <div class="content">
                    <h2>Hello {author_name}!</h2>
                    <p>Great news! Your recipe has received a new rating.</p>
                    
                    <div class="rating-box">
                        <div class="stars">{stars}</div>
                        <div class="recipe-title">{recipe_title}</div>
                        <div class="reviewer">Rated by {reviewer_name}</div>
                    </div>
                    
                    <p>Keep creating delicious recipes!</p>
                    
                    <p>Best regards,<br>The CulinaryVerse Team</p>
                </div>
                <div class="footer">
                    <p>© 2024 CulinaryVerse. All rights reserved.</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text content (fallback)
        text_content = f"""
        CulinaryVerse - New Rating Notification
        
        Hello {author_name},
        
        Great news! Your recipe "{recipe_title}" has received a new rating.
        
        Rating: {stars} ({rating_value}/5 stars)
        Rated by: {reviewer_name}
        
        Keep creating delicious recipes!
        
        Best regards,
        The CulinaryVerse Team
        """
        
        # Attach both parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"Rating notification sent to {author_email}")
        return True
    except Exception as e:
        print(f"Error sending rating notification: {e}")
        return False
