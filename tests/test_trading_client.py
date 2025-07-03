import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from trading_client import RecallTradingClient, Token, Balance

class TestRecallTradingClient(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('trading_client.Config') as mock_config:
            mock_config.TRADING_SIM_API_KEY = "test_api_key"
            mock_config.TRADING_SIM_API_URL = "https://test.api.com"
            self.client = RecallTradingClient()
    
    def test_initialization(self):
        """Test client initialization"""
        self.assertIsNotNone(self.client.api_key)
        self.assertIsNotNone(self.client.base_url)
        self.assertIn("Authorization", self.client.session.headers)
    
    @patch('trading_client.requests.Session.get')
    def test_get_portfolio_success(self, mock_get):
        """Test successful portfolio retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total_value": 1000.0}
        mock_get.return_value = mock_response
        
        result = self.client.get_portfolio()
        
        self.assertEqual(result["total_value"], 1000.0)
        mock_get.assert_called_once()
    
    @patch('trading_client.requests.Session.get')
    def test_get_balances_success(self, mock_get):
        """Test successful balances retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "balances": [
                {
                    "token": {
                        "address": "0x123",
                        "symbol": "WETH",
                        "chain": "ethereum",
                        "decimals": 18
                    },
                    "amount": "1.5",
                    "usd_value": "3000.0"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        balances = self.client.get_balances()
        
        self.assertEqual(len(balances), 1)
        self.assertIsInstance(balances[0], Balance)
        self.assertEqual(balances[0].token.symbol, "WETH")
        self.assertEqual(balances[0].amount, 1.5)
    
    @patch('trading_client.requests.Session.post')
    def test_execute_trade_success(self, mock_post):
        """Test successful trade execution"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tx_hash": "0xabc123", "status": "success"}
        mock_post.return_value = mock_response
        
        result = self.client.execute_trade(
            from_token="0x123",
            to_token="0x456",
            amount=100.0,
            reason="Test trade"
        )
        
        self.assertEqual(result["status"], "success")
        mock_post.assert_called_once()
    
    def test_health_check_success(self):
        """Test successful health check"""
        with patch('trading_client.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = self.client.health_check()
            
            self.assertTrue(result)
    
    def test_health_check_failure(self):
        """Test failed health check"""
        with patch('trading_client.requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            result = self.client.health_check()
            
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()