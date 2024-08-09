from flask import Flask, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import re

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to remove HTML tags from a string
def strip_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# Send email function
def send_email(from_addr, password, to_addrs, cc_addrs, bcc_addrs, subject, body, attachments):
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = ', '.join(to_addrs)
    msg['Cc'] = ', '.join(cc_addrs)
    msg['Bcc'] = ', '.join(bcc_addrs)
    msg['Subject'] = subject

    # Attach plain text body (with HTML stripped)
    msg.attach(MIMEText(body, 'plain'))

    for attachment in attachments:
        with open(attachment, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment)}")
            msg.attach(part)

    text = msg.as_string()

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(from_addr, password)
            server.sendmail(from_addr, to_addrs + cc_addrs + bcc_addrs, text)
        return {"status": "success", "message": "Email sent successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/send-email', methods=['POST'])
def handle_send_email():
    data = request.form

    # Check if fields are received; if not, default to an empty string or an empty list
    from_addr = data.get('from_addr', '')
    password = data.get('password', '')
    to_addrs = data.get('to_addrs', '').split(',')
    cc_addrs = data.get('cc_addrs', '').split(',')
    bcc_addrs = data.get('bcc_addrs', '').split(',')
    subject = data.get('subject', '')
    body = data.get('body', '')

    # Remove HTML tags from the body
    body = strip_html_tags(body)

    # Save attachments and get file paths
    attachments = []
    for file in request.files.getlist('attachments'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        attachments.append(filepath)

    # Send email
    result = send_email(from_addr, password, to_addrs, cc_addrs, bcc_addrs, subject, body, attachments)
    return jsonify(result)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
