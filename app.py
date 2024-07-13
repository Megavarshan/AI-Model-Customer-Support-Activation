import openai
import logging
from flask import Flask, render_template, request, jsonify
from transformers import pipeline
from googletrans import Translator
import json
from kafka import KafkaConsumer
import threading

# Initialize OpenAI, sentiment analysis, and translator
openai.api_key = 'YOUR_API_KEY'
sentiment_analyzer = pipeline('sentiment-analysis')
translator = Translator()

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Context Manager to maintain conversation history
class ContextManager:
    def __init__(self):
        self.context = {}

    def update_context(self, user_id, new_context):
        if user_id in self.context:
            self.context[user_id] += ' ' + new_context
        else:
            self.context[user_id] = new_context

    def get_context(self, user_id):
        return self.context.get(user_id, '')

context_manager = ContextManager()

def analyze_sentiment(text):
    return sentiment_analyzer(text)[0]

def translate_text(text, target_language='en'):
    translation = translator.translate(text, dest=target_language)
    return translation.text

def generate_response(user_id, prompt):
    context = context_manager.get_context(user_id)
    full_prompt = f"Context: {context}\nUser Query: {prompt}"
    logger.info(f"Generating response for user_id: {user_id} with prompt: {full_prompt}")
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=full_prompt,
        max_tokens=150
    ).choices[0].text.strip()
    context_manager.update_context(user_id, f"User Query: {prompt}\nAI Response: {response}")
    return response

def fetch_customer_data(customer_id):
    customer_data = {
        "name": "John Doe",
        "purchase_history": ["laptop", "mouse"],
        "preferences": ["tech", "gadgets"],
        "last_interaction": "2024-07-01"
    }
    logger.info(f"Fetched customer data for customer_id: {customer_id}")
    return customer_data

def generate_personalized_message(customer_id, prompt):
    customer_data = fetch_customer_data(customer_id)
    personalized_prompt = f"{prompt}\nCustomer Data: {json.dumps(customer_data)}"
    logger.info(f"Generating personalized message for customer_id: {customer_id} with prompt: {personalized_prompt}")
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=personalized_prompt,
        max_tokens=150
    ).choices[0].text.strip()
    return response

# Flask app for real-time interaction
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_response', methods=['POST'])
def generate_response_route():
    data = request.json
    user_id = data['user_id']
    query = data['query']
    sentiment = analyze_sentiment(query)
    logger.info(f"User Query: {query}, Sentiment: {sentiment}")
    response = generate_response(user_id, query)
    translated_response = translate_text(response, data.get('preferred_language', 'en'))
    return jsonify({
        'sentiment': sentiment,
        'response': translated_response
    })

@app.route('/generate_personalized_message', methods=['POST'])
def generate_personalized_message_route():
    data = request.json
    customer_id = data['customer_id']
    prompt = data['prompt']
    response = generate_personalized_message(customer_id, prompt)
    translated_response = translate_text(response, data.get('preferred_language', 'en'))
    return jsonify({
        'response': translated_response
    })

# Function to update customer data in real-time
def update_customer_data():
    consumer = KafkaConsumer(
        'customer-data',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='customer-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    for message in consumer:
        customer_id = message.value['customer_id']
        new_data = message.value['data']
        # Update customer data logic here
        logger.info(f"Updated customer data for customer_id: {customer_id} with new data: {new_data}")

# Start a background thread to listen for real-time updates
update_thread = threading.Thread(target=update_customer_data)
update_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
