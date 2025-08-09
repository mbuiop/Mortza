from flask import Flask, render_template, request, jsonify
import openai
import os

app = Flask(__name__)

# تنظیم کلید API OpenAI - لطفاً این را در محیط واقعی در یک فایل محیطی یا مدیریت رمز عبور امن ذخیره کنید
openai.api_key = "sk-ant-api03-srD...swAA"  # کلید واقعی خود را اینجا قرار دهید

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['message']
    
    try:
        # ارسال درخواست به OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # یا مدل دیگری که می‌خواهید استفاده کنید
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        
        assistant_reply = response.choices[0].message['content']
        return jsonify({'reply': assistant_reply})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
