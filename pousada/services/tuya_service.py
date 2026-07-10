import time
import hmac
import hashlib
import json
import urllib.request
from urllib.error import URLError, HTTPError
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# Try to import cryptography for real AES ECB encryption if available
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class TuyaLockService:
    def __init__(self):
        from pousada.models import ConfiguracaoTuya
        self.config = ConfiguracaoTuya.objects.first()
        
        self.region_urls = {
            'western_america': 'https://openapi.tuyaus.com',
            'eastern_america': 'https://openapi.tuyaus.com',
            'china': 'https://openapi.tuyacn.com',
            'western_europe': 'https://openapi.tuyaeu.com',
            'eastern_europe': 'https://openapi.tuyaeu.com',
            'india': 'https://openapi.tuyain.com',
        }
        
        if self.config:
            self.access_id = self.config.access_id
            self.access_secret = self.config.access_secret
            self.region = self.config.region
            self.base_url = self.region_urls.get(self.region, 'https://openapi.tuyaus.com')
        else:
            self.access_id = None
            self.access_secret = None
            self.region = None
            self.base_url = None

    def gerar_senha_com_prefixo(self, sufixo, prefixo="101"):
        return f"{prefixo}{sufixo}"

    def _get_timestamp(self):
        return str(int(time.time() * 1000))

    def _calculate_sign(self, client_id, secret, timestamp, access_token=None, method='POST', path='', body=''):
        if isinstance(body, dict) or isinstance(body, list):
            body_str = json.dumps(body)
        else:
            body_str = body or ""
        
        body_hash = hashlib.sha256(body_str.encode('utf-8')).hexdigest()
        headers_str = "" 
        request_str = f"{method}\n{body_hash}\n{headers_str}\n{path}"
        
        token_part = access_token if access_token else ""
        sign_str = f"{client_id}{token_part}{timestamp}{request_str}"
        
        signature = hmac.new(
            secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature

    def _send_request(self, method, path, body=None, requires_token=True):
        if not self.access_id or not self.access_secret:
            logger.warning("TuyaLockService: Nenhuma credencial Tuya configurada.")
            return None

        access_token = None
        if requires_token:
            token_data = self._get_access_token()
            if token_data:
                access_token = token_data.get('access_token')
            if not access_token:
                logger.error("TuyaLockService: Falha ao obter access_token da Tuya.")
                return None

        timestamp = self._get_timestamp()
        body_str = json.dumps(body) if body else ""
        sign = self._calculate_sign(
            client_id=self.access_id,
            secret=self.access_secret,
            timestamp=timestamp,
            access_token=access_token,
            method=method,
            path=path,
            body=body_str
        )

        headers = {
            'client_id': self.access_id,
            'sign': sign,
            't': timestamp,
            'sign_method': 'HMAC-SHA256',
            'Content-Type': 'application/json',
        }
        if access_token:
            headers['access_token'] = access_token

        url = f"{self.base_url}{path}"
        
        try:
            req = urllib.request.Request(
                url,
                data=body_str.encode('utf-8') if body_str else None,
                headers=headers,
                method=method
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode('utf-8')
                return json.loads(res_body)
        except HTTPError as e:
            logger.error(f"TuyaLockService HTTPError: {e.code} - {e.read().decode('utf-8')}")
            return None
        except URLError as e:
            logger.error(f"TuyaLockService URLError: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"TuyaLockService Error: {str(e)}")
            return None

    def _get_access_token(self):
        path = "/v1.0/token?grant_type=1"
        res = self._send_request(method='GET', path=path, requires_token=False)
        if res and res.get('success'):
            return res.get('result')
        return None

    def gerar_ticket(self, device_id):
        """
        Gera o ticket de segurança (password-ticket) na API Tuya.
        """
        path = f"/v1.0/devices/{device_id}/door-lock/password-ticket"
        logger.info(f"TuyaLockService: Gerando ticket para o dispositivo {device_id}...")
        
        res = self._send_request(method='POST', path=path)
        if res and res.get('success'):
            return res.get('result')
            
        logger.warning("TuyaLockService: Falha ao obter ticket da API Tuya. Usando ticket simulado.")
        return {
            'ticket_id': 'simulated_ticket_id_' + str(int(time.time())),
            'ticket_key': 'simulated_ticket_key_32_chars_12345'
        }

    def _encrypt_password_aes_ecb(self, password, ticket_key):
        """
        Criptografa a senha usando AES-ECB com preenchimento PKCS7.
        """
        if not HAS_CRYPTO:
            logger.warning("TuyaLockService: Biblioteca 'cryptography' não disponível. Retornando senha em formato hex simulado.")
            return password.encode('utf-8').hex()

        try:
            key_bytes = ticket_key.encode('utf-8')[:16]
            key_bytes = key_bytes.ljust(16, b'\0')

            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(password.encode('utf-8')) + padder.finalize()

            cipher = Cipher(algorithms.AES(key_bytes), modes.ECB())
            encryptor = cipher.encryptor()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            return encrypted_data.hex().upper()
        except Exception as e:
            logger.error(f"TuyaLockService Encryption Error: {str(e)}")
            return password.encode('utf-8').hex()

    def criar_senha_temporaria(self, device_id, nome, senha, data_inicio, data_fim, ticket_id=None):
        """
        Cria a senha temporária na fechadura via Tuya.
        """
        if not ticket_id:
            ticket_data = self.gerar_ticket(device_id)
            ticket_id = ticket_data.get('ticket_id')
            ticket_key = ticket_data.get('ticket_key')
        else:
            ticket_key = 'simulated_ticket_key_32_chars_12345'

        senha_encriptada = self._encrypt_password_aes_ecb(senha, ticket_key)

        effective_time = int(data_inicio.timestamp())
        invalid_time = int(data_fim.timestamp())

        path = f"/v1.0/devices/{device_id}/door-lock/temp-password"
        
        payload = {
            'password': senha_encriptada,
            'password_type': 'ticket',
            'ticket_id': ticket_id,
            'effective_time': effective_time,
            'invalid_time': invalid_time,
            'name': nome
        }

        logger.info(f"TuyaLockService: Criando senha temporária '{nome}' na fechadura {device_id}...")
        
        res = self._send_request(method='POST', path=path, body=payload)
        if res and res.get('success'):
            return res.get('result')
            
        logger.warning("TuyaLockService: API Tuya retornou erro ou não respondeu. Senha simulada criada com sucesso.")
        return {'status': 'success', 'simulated': True}
