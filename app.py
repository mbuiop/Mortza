from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# تنظیمات Claude API
CLAUDE_API_KEY = "sk-ant-api03-srD...swAA"  # کلید API خود را اینجا قرار دهید
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['message']
    
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-3-opus-20240229",  # می‌توانید مدل را تغییر دهید
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": user_message}]
    }
    
    try:
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        assistant_reply = response.json()["content"][0]["text"]
        return jsonify({'reply': assistant_reply})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
