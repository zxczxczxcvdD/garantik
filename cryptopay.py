import requests
from config import CRYPTOPAY_API_TOKEN, CRYPTOPAY_API_URL

class CryptoPay:
    def __init__(self, api_token=None):
        self.api_token = api_token or CRYPTOPAY_API_TOKEN
        self.base_url = CRYPTOPAY_API_URL
    
    def create_invoice(self, amount, currency='USDT', description=None):
        """
        Создает счет через CryptoPay API
        """
        url = f"{self.base_url}/createInvoice"
        headers = {
            'Crypto-Pay-API-Token': self.api_token
        }
        data = {
            'asset': currency,
            'amount': str(amount),
        }
        if description:
            data['description'] = description
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('ok'):
                invoice_data = result.get('result', {})
                return {
                    'success': True,
                    'invoice_id': invoice_data.get('invoice_id'),
                    'pay_url': invoice_data.get('pay_url'),
                    'invoice_url': invoice_data.get('pay_url')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('name', 'Unknown error')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_invoice_status(self, invoice_id):
        """
        Проверяет статус счета
        """
        url = f"{self.base_url}/getInvoices"
        headers = {
            'Crypto-Pay-API-Token': self.api_token
        }
        params = {
            'invoice_ids': str(invoice_id)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            if result.get('ok'):
                invoices = result.get('result', {}).get('items', [])
                if invoices:
                    invoice = invoices[0]
                    return {
                        'success': True,
                        'status': invoice.get('status'),
                        'paid': invoice.get('status') == 'paid',
                        'amount': invoice.get('amount'),
                        'paid_amount': invoice.get('paid_amount')
                    }
            return {
                'success': False,
                'error': 'Invoice not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def transfer(self, user_id, amount, asset='USDT', spend_id=None):
        """
        Переводит средства пользователю через CryptoPay
        """
        url = f"{self.base_url}/transfer"
        headers = {
            'Crypto-Pay-API-Token': self.api_token
        }
        data = {
            'user_id': user_id,
            'asset': asset,
            'amount': str(amount)
        }
        if spend_id:
            data['spend_id'] = str(spend_id)
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('ok'):
                return {
                    'success': True,
                    'transfer_id': result.get('result', {}).get('transfer_id')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('name', 'Unknown error')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

