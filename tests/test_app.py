import unittest
import json
from app import app

class TestAntifraudeApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_validate_approved(self):
        response = self.app.post('/validate', 
                                 json={'amount': 500, 'card_number': '4222222222222222', 'country': 'AR'},
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'APPROVED')

    def test_validate_rejected_high_amount(self):
        response = self.app.post('/validate', 
                                 json={'amount': 1500, 'card_number': '4222222222222222', 'country': 'AR'},
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'REJECTED')
        self.assertEqual(data['reason'], 'Amount exceeds limit')

    def test_validate_rejected_invalid_card(self):
        response = self.app.post('/validate', 
                                 json={'amount': 500, 'card_number': '123', 'country': 'AR'},
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'REJECTED')
        self.assertEqual(data['reason'], 'Invalid card number')

if __name__ == '__main__':
    unittest.main()
