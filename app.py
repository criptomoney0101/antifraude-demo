from flask import Flask, request, jsonify
import re
import os
from datetime import datetime

app = Flask(__name__)

# Reglas antifraude
FRAUD_RULES = {
    'max_amount': 1000,
    'suspicious_countries': ['XX', 'YY'],
    'high_risk_cards': ['4111111111111111']
}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/validate', methods=['POST'])
def validate_transaction():
    data = request.json
    amount = data.get('amount', 0)
    card_number = data.get('card_number', '')
    country = data.get('country', '')
    
    # Validación básica
    if not re.match(r'^\d{16}$', card_number):
        return jsonify({"status": "REJECTED", "reason": "Invalid card number"})
    
    # Regla 1: Monto máximo
    if amount > FRAUD_RULES['max_amount']:
        return jsonify({"status": "REJECTED", "reason": "Amount exceeds limit"})
    
    # Regla 2: País sospechoso
    if country in FRAUD_RULES['suspicious_countries']:
        return jsonify({"status": "REJECTED", "reason": "Suspicious country"})
    
    # Regla 3: Tarjeta de alto riesgo
    if card_number in FRAUD_RULES['high_risk_cards']:
        return jsonify({"status": "REJECTED", "reason": "High risk card"})
    
    return jsonify({"status": "APPROVED", "validation_id": f"TXN_{datetime.utcnow().timestamp()}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
