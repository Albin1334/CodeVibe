from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import time

app = Flask(__name__, static_folder='.')
CORS(app)

# Create uploads folder for skin images
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ============ OPENROUTER API CONFIGURATION ============
OPENROUTER_API_KEY = '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'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# System prompt for medical triage
SYSTEM_PROMPT = """You are Healthify, an AI medical triage nurse. Analyze symptoms and respond with JSON only.

Respond ONLY with this exact JSON format (no markdown):
{
    "severity_level": "HOME_CARE or CONSULT_GP or EMERGENCY",
    "spoken_response": "Friendly 2-3 sentence response",
    "detailed_plan": "Care instructions as bullet points",
    "medications": [{"name": "Medicine name", "dosage": "How to take", "type": "OTC"}],
    "home_remedies": ["Remedy 1 with emoji", "Remedy 2 with emoji"],
    "verified_sources": ["https://www.nhs.uk/..."]
}

Rules:
- Always separate medications (OTC only) and home remedies
- Be empathetic and professional
- Chest pain/breathing issues = EMERGENCY"""

# ============ ROBUST DATABASES ============
SKIN_CONDITIONS = {
    'eczema': {
        'keywords': ['eczema', 'dry patches', 'itchy dry', 'scaly', 'red dry', 'flaky'],
        'condition_name': 'Eczema',
        'description': 'Chronic skin condition causing dry, itchy, inflamed patches.',
        'severity': 'CONSULT_GP',
        'medications': [{'name': 'Hydrocortisone 1%', 'dosage': '2x daily', 'type': 'OTC'}, {'name': 'Cetirizine', 'dosage': '10mg daily', 'type': 'OTC'}],
        'home_remedies': ['🥥 Coconut oil', '🛁 Oatmeal bath', '❄️ Cool compress'],
        'when_to_see_doctor': 'If infected or persisting >2 weeks.',
        'sources': ['https://www.nhs.uk/conditions/atopic-eczema/']
    },
    'acne': {
        'keywords': ['acne', 'pimples', 'zits', 'blackheads', 'breakout'],
        'condition_name': 'Acne',
        'description': 'Common condition causing pimples and oily skin.',
        'severity': 'HOME_CARE',
        'medications': [{'name': 'Benzoyl Peroxide', 'dosage': 'Daily', 'type': 'OTC'}, {'name': 'Salicylic Acid', 'dosage': 'Wash 2x daily', 'type': 'OTC'}],
        'home_remedies': ['🧊 Ice for swelling', '🍵 Tea tree oil', '🥒 Aloe vera'],
        'when_to_see_doctor': 'If severe or scarring occurs.',
        'sources': ['https://www.nhs.uk/conditions/acne/']
    },
    'hives': {
        'keywords': ['hives', 'welts', 'urticaria', 'allergic rash'],
        'condition_name': 'Hives',
        'description': 'Raised, itchy welts from allergic reaction.',
        'severity': 'CONSULT_GP',
        'medications': [{'name': 'Benadryl', 'dosage': '25mg q6h', 'type': 'OTC'}, {'name': 'Zyrtec', 'dosage': '10mg daily', 'type': 'OTC'}],
        'home_remedies': ['❄️ Cold compress', '🛁 Cool bath', '👕 Loose clothing'],
        'when_to_see_doctor': 'EMERGENCY if breathing affected.',
        'sources': ['https://www.nhs.uk/conditions/hives/']
    }
}

SYMPTOM_DATABASE = {
    'headache': {
        'severity': 'HOME_CARE',
        'spoken': 'Headaches are common. Dehydration is a frequent cause.',
        'plan': '**Care:**\n• Drink water\n• Rest in dark room\n• Cold compress',
        'meds': [{'name': 'Paracetamol', 'dosage': '500-1000mg q4-6h', 'type': 'OTC'}, {'name': 'Ibuprofen', 'dosage': '400mg q6h', 'type': 'OTC'}],
        'remedies': ['💧 Hydration', '❄️ Cold pack', '💆 Massage', '😴 Sleep'],
        'sources': ['https://www.nhs.uk/conditions/headaches/']
    },
    'fever': {
        'severity': 'CONSULT_GP',
        'spoken': 'Fever means your body is fighting something. Monitor temperature closely.',
        'plan': '**Care:**\n• Rest\n• Fluids\n• Monitor temp',
        'meds': [{'name': 'Paracetamol', 'dosage': '500mg q4-6h', 'type': 'OTC'}, {'name': 'Ibuprofen', 'dosage': '400mg q6h', 'type': 'OTC'}],
        'remedies': ['💧 Fluids', '🚿 Lukewarm bath', '🛏️ Rest'],
        'sources': ['https://www.nhs.uk/conditions/fever-in-adults/']
    },
    'cold': {
        'severity': 'HOME_CARE',
        'spoken': 'Colds usually last a week. Rest and fluids are key.',
        'plan': '**Care:**\n• Rest\n• Hydrate\n• Steam',
        'meds': [{'name': 'Decongestant', 'dosage': 'As directed', 'type': 'OTC'}, {'name': 'Paracetamol', 'dosage': '500mg as needed', 'type': 'OTC'}],
        'remedies': ['🍜 Soup', '🍯 Honey tea', '😤 Steam', '😴 Sleep'],
        'sources': ['https://www.nhs.uk/conditions/common-cold/']
    },
    'cough': {
        'severity': 'HOME_CARE',
        'spoken': 'Coughs can linger but usually clear up. Honey helps soothe the throat.',
        'plan': '**Care:**\n• Honey & lemon\n• Hydration\n• Humidifier',
        'meds': [{'name': 'Guaifenesin', 'dosage': 'As directed', 'type': 'OTC'}, {'name': 'Cough Drops', 'dosage': 'As needed', 'type': 'OTC'}],
        'remedies': ['🍯 Honey', '🍵 Warm tea', '💧 Fluids'],
        'sources': ['https://www.nhs.uk/conditions/cough/']
    },
    'cuts': {
        'severity': 'HOME_CARE',
        'spoken': 'Clean the wound immediately. Apply pressure to stop bleeding.',
        'plan': '**Wound Care:**\n• Wash with soap & water\n• Apply pressure if bleeding\n• Apply antibiotic ointment\n• Cover with bandage',
        'meds': [{'name': 'Neosporin', 'dosage': 'Apply to wound', 'type': 'OTC'}, {'name': 'Band-Aids', 'dosage': 'Cover wound', 'type': 'Supply'}],
        'remedies': ['🧼 Clean thoroughly', '🩹 Keep dry', '🍯 Honey (antibacterial)'],
        'sources': ['https://www.nhs.uk/conditions/cuts-and-grazes/']
    },
    'rusty': {
        'severity': 'CONSULT_GP',
        'spoken': 'Rusty object injuries vary in risk. A Tetanus shot may be needed if yours is out of date.',
        'plan': '**Safety Steps:**\n• Clean thoroughly\n• Check Tetanus shot status (needed every 10 years)\n• Watch for infection',
        'meds': [{'name': 'Antibiotic Ointment', 'dosage': 'Apply to wound', 'type': 'OTC'}, {'name': 'Ibuprofen', 'dosage': 'For pain/swelling', 'type': 'OTC'}],
        'remedies': ['🧼 Wash immediately', '🏥 visit clinic if deep', '💉 Check Tetanus status'],
        'sources': ['https://www.cdc.gov/tetanus/index.html']
    },
    'period': {
        'severity': 'HOME_CARE',
        'spoken': 'Period pain is common. Heat and OTC pain relief usually help.',
        'plan': '**Period Care:**\n• Use heat pad\n• Rest\n• Stay hydrated\n• Light exercise',
        'meds': [{'name': 'Ibuprofen (Advil)', 'dosage': '400mg every 6h', 'type': 'OTC'}, {'name': 'Naproxen (Aleve)', 'dosage': '220mg every 8-12h', 'type': 'OTC'}, {'name': 'Midol', 'dosage': 'As directed', 'type': 'OTC'}],
        'remedies': ['🔥 Heating pad', '🍫 Dark chocolate', '🍵 Ginger tea', '🧘 Gentle yoga'],
        'sources': ['https://www.nhs.uk/conditions/period-pain/']
    },
    'menstrual': {
        'severity': 'HOME_CARE',
        'spoken': 'Menstrual cramps can be managed with heat and rest.',
        'plan': '**Cramp Relief:**\n• Apply heat to lower belly\n• Drink warm herbal tea\n• Warm bath',
        'meds': [{'name': 'Ibuprofen', 'dosage': '400mg every 4-6h', 'type': 'OTC'}, {'name': 'Naproxen', 'dosage': '220mg every 8-12h', 'type': 'OTC'}],
        'remedies': ['🔥 Hot water bottle', '🥬 Magnesium rich foods', '🛌 Rest'],
        'sources': ['https://www.nhs.uk/conditions/period-pain/']
    },
    'sore throat': {
        'severity': 'HOME_CARE',
        'spoken': 'Most sore throats are viral. Salt water gargles help significantly.',
        'plan': '**Care:**\n• Salt gargle\n• Warm fluids\n• Rest voice',
        'meds': [{'name': 'Lozenges', 'dosage': 'Every 2-3h', 'type': 'OTC'}, {'name': 'Ibuprofen', 'dosage': '400mg q6h', 'type': 'OTC'}],
        'remedies': ['🧂 Salt water', '🍯 Honey', '🍦 Ice chips'],
        'sources': ['https://www.nhs.uk/conditions/sore-throat/']
    }
}

def call_openrouter_api(messages):
    """Call API with short timeout"""
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'Healthify'
    }
    
    payload = {
        'model': 'google/gemini-2.0-flash-001',
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 1000
    }
    
    try:
        # Reduced timeout to 8 seconds to prevent hanging
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=8)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/analyze-skin', methods=['POST'])
def analyze_skin():
    description = request.form.get('description', '').strip().lower()
    
    # Handle optional image
    if 'image' in request.files:
        try:
            file = request.files['image']
            if file.filename:
                file.save(os.path.join(UPLOAD_FOLDER, f"skin_{int(time.time())}.jpg"))
        except: pass
    
    if not description:
        return jsonify({'error': 'No description'}), 400

    # 1. Try Dictionary Match First (Instant)
    for key, data in SKIN_CONDITIONS.items():
        if any(kw in description for kw in data['keywords']):
            colors = {'HOME_CARE': 'green', 'CONSULT_GP': 'yellow', 'EMERGENCY': 'red'}
            return jsonify({
                'matched': True,
                'condition_name': data['condition_name'],
                'description': data['description'],
                'severity_level': data['severity'],
                'severity_color': colors.get(data['severity'], 'yellow'),
                'medications': data['medications'],
                'home_remedies': data['home_remedies'],
                'when_to_see_doctor': data['when_to_see_doctor'],
                'sources': data['sources']
            })

    # 2. Try AI if no match
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"Skin condition: {description}"}
    ]
    
    api_response = call_openrouter_api(messages)
    
    if api_response and 'choices' in api_response:
        try:
            text = api_response['choices'][0]['message']['content'].strip()
            if '```' in text:
                text = text.split('```')[1].replace('json', '').strip()
            
            res = json.loads(text)
            colors = {'HOME_CARE': 'green', 'CONSULT_GP': 'yellow', 'EMERGENCY': 'red'}
            
            return jsonify({
                'matched': True,
                'condition_name': res.get('condition_name', 'Skin Condition'),
                'description': res.get('spoken_response', 'Analyzed via AI'),
                'severity_level': res.get('severity_level', 'CONSULT_GP'),
                'severity_color': colors.get(res.get('severity_level'), 'yellow'),
                'medications': res.get('medications', []),
                'home_remedies': res.get('home_remedies', []),
                'when_to_see_doctor': 'Consult a doctor for advice.',
                'sources': res.get('verified_sources', [])
            })
        except: pass

    # 3. Fallback
    return jsonify({
        'matched': False,
        'condition_name': 'Unknown Condition',
        'description': 'Please consult a dermatologist.',
        'severity_level': 'CONSULT_GP',
        'severity_color': 'yellow',
        'medications': [],
        'home_remedies': ['👨‍⚕️ Consult a doctor', '📸 Take photos'],
        'when_to_see_doctor': 'See a doctor.',
        'sources': []
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_symptoms():
    data = request.get_json()
    symptoms = data.get('symptoms', '').strip().lower()
    
    if not symptoms:
        return jsonify({'error': 'No symptoms'}), 400

    # 1. Try Dictionary Match First for Speed
    for key, data in SYMPTOM_DATABASE.items():
        if key in symptoms:
            colors = {'HOME_CARE': 'green', 'CONSULT_GP': 'yellow', 'EMERGENCY': 'red'}
            return jsonify({
                'severity_level': data['severity'],
                'severity_color': colors.get(data['severity'], 'yellow'),
                'spoken_response': data['spoken'],
                'detailed_plan': data['plan'],
                'medications': data['meds'],
                'home_remedies': data['remedies'],
                'verified_sources': data['sources']
            })

    # 2. Try AI for complex/unknown queries
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': f"Symptoms: {symptoms}"}
    ]
    
    api_response = call_openrouter_api(messages)
    
    if api_response and 'choices' in api_response:
        try:
            text = api_response['choices'][0]['message']['content'].strip()
            if '```' in text:
                text = text.split('```')[1].replace('json', '').strip()
            
            res = json.loads(text)
            colors = {'HOME_CARE': 'green', 'CONSULT_GP': 'yellow', 'EMERGENCY': 'red'}
            res['severity_color'] = colors.get(res.get('severity_level'), 'yellow')
            return jsonify(res)
        except: pass

    # 3. Ultimate Fallback
    return jsonify({
        'severity_level': 'CONSULT_GP',
        'severity_color': 'yellow',
        'spoken_response': 'I recommend consulting a healthcare professional.',
        'detailed_plan': '**Guidance:**\n• Monitor symptoms\n• Stay hydrated\n• Contact GP',
        'medications': [],
        'home_remedies': ['📝 Track symptoms', '👨‍⚕️ See doctor'],
        'verified_sources': ['https://www.nhs.uk/']
    })

if __name__ == '__main__':
    print("=" * 50)
    print("[HEALTHIFY] Hybrid AI + Dictionary System")
    print("=" * 50)
    print("[*] Running on http://localhost:5000")
    app.run(debug=True, port=5000)
