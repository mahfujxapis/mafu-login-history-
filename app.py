#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Free Fire Login History API - Production Version
Optimized for Render/Vercel Deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import requests
import base64
import json
from datetime import datetime
import traceback
import os
import logging

# --- Logging Setup for Production ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Simple Color Simulation (no colorama dependency issues) ---
class Colors:
    GREEN = '\033[92m' if os.name == 'posix' else ''
    YELLOW = '\033[93m' if os.name == 'posix' else ''
    RED = '\033[91m' if os.name == 'posix' else ''
    CYAN = '\033[96m' if os.name == 'posix' else ''
    MAGENTA = '\033[95m' if os.name == 'posix' else ''
    RESET = '\033[0m' if os.name == 'posix' else ''

# --- Protobuf Module Import with Fallback ---
try:
    import LoginHistory_pb2
    PROTOBUF_AVAILABLE = True
    logger.info(f"{Colors.GREEN}✅ Protobuf module loaded successfully{Colors.RESET}")
except ImportError as e:
    PROTOBUF_AVAILABLE = False
    logger.error(f"{Colors.RED}❌ LoginHistory_pb2.py not found!{Colors.RESET}")
    logger.error(f"{Colors.YELLOW}Make sure LoginHistory_pb2.py is in the same directory{Colors.RESET}")

# --- Flask Setup ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Channel & Developer Info ---
CHANNEL_INFO = {
    "main_channel": "@mahfuj_offcial",
    "api_channel": "@mafuapis",
    "developer": "@mahfuj_offcial_143"
}

# --- Secret Key for Decryption ---
SECRET_KEY = b"1e5898ccb8dfdd921f9bdea848768b64a201"

# ============================================
# 🛠️ UTILITY FUNCTIONS
# ============================================

def decode_nickname(encoded: str) -> str:
    """XOR + Base64 decrypt nickname from JWT"""
    try:
        raw = base64.b64decode(encoded)
        dec = bytearray()
        for i, b in enumerate(raw):
            dec.append(b ^ SECRET_KEY[i % len(SECRET_KEY)])
        return dec.decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Nickname decode error: {e}")
        return f"[DECODE_ERROR]"

def decode_jwt(token: str) -> dict:
    """Decode JWT token and extract profile data"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}
        
        payload_b64 = parts[1]
        # Fix base64 padding
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += '=' * padding
        
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        
        if 'nickname' in payload and isinstance(payload['nickname'], str):
            payload['nickname'] = decode_nickname(payload['nickname'])
        
        return payload
    except Exception as e:
        logger.error(f"JWT decode error: {e}")
        return {"error": str(e)}

def get_base_url(region: str) -> str:
    """Get API base domain by region code"""
    r = region.upper() if region else 'UNKNOWN'
    region_map = {
        'IND': 'client.ind.freefiremobile.com',
        'BR': 'client.us.freefiremobile.com',
        'US': 'client.us.freefiremobile.com',
        'NA': 'client.us.freefiremobile.com',
        'SAC': 'client.us.freefiremobile.com'
    }
    return region_map.get(r, 'clientbp.ggpolarbear.com')

def format_timestamp(ts) -> dict:
    """Convert Unix timestamp to readable formats"""
    try:
        if not ts:
            return {"timestamp": 0, "error": "No timestamp"}
        dt = datetime.fromtimestamp(ts)
        return {
            "timestamp": ts,
            "datetime": dt.strftime('%Y-%m-%d %H:%M:%S'),
            "date": dt.strftime('%Y-%m-%d'),
            "time": dt.strftime('%H:%M:%S'),
            "day": dt.strftime('%A'),
            "iso": dt.isoformat()
        }
    except Exception as e:
        return {"timestamp": ts, "error": str(e)}

def fetch_login_history(token: str) -> dict:
    """Main function to fetch and parse login history from Free Fire API"""
    
    if not PROTOBUF_AVAILABLE:
        return {
            "success": False, 
            "error": "Protobuf module not available. Please ensure LoginHistory_pb2.py is present."
        }
    
    # Step 1: Decode JWT
    jwt_payload = decode_jwt(token)
    if 'error' in jwt_payload:
        return {"success": False, "error": f"JWT decode failed: {jwt_payload['error']}"}
    
    nickname = jwt_payload.get('nickname', 'N/A')
    account_id = jwt_payload.get('account_id', 'N/A')
    region = jwt_payload.get('lock_region') or jwt_payload.get('region')
    
    if not region:
        return {"success": False, "error": "Region not found in token"}
    
    # Step 2: Prepare API Request
    base_domain = get_base_url(region)
    url = f"https://{base_domain}/GetLoginHistory"
    
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; Build/QP1A.190711.020)',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
        'Authorization': f'Bearer {token}',
        'X-Unity-Version': '2018.4.11f1',
        'X-GA': 'v1 1',
        'ReleaseVersion': 'OB53',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Hardcoded protobuf payload
    payload_hex = 'ac74dc5eb016b4ed43774eec3d13e042bd8faa337913efeb6b92ddfbf113c5cd7972e5a9fee97dc9aa8a71270cae1dc9902c91a5eeee312684d4834c003fcf7d83067c9157de749063ed0714b442666c'
    
    try:
        raw_body = bytes.fromhex(payload_hex)
    except ValueError as e:
        return {"success": False, "error": f"Hex decode error: {e}"}
    
    # Step 3: Send Request
    try:
        resp = requests.post(url, headers=headers, data=raw_body, timeout=30)
        
        if resp.status_code != 200:
            return {
                "success": False,
                "error": f"Free Fire API returned status {resp.status_code}",
                "status_code": resp.status_code
            }
        
        # Step 4: Parse Protobuf Response
        login_history = LoginHistory_pb2.LoginHistory()
        login_history.ParseFromString(resp.content)
        
        # Step 5: Build JSON Response
        entries = []
        usual_count = 0
        unusual_count = 0
        
        for entry in login_history.login_entries:
            # Determine login type
            if entry.LoginType in [1, 2]:  # USUAL or USUAL_LOGIN
                login_type = "usual"
                usual_count += 1
            elif entry.LoginType in [3, 4]:  # UNUSUAL or UNUSUAL_LOGIN
                login_type = "unusual"
                unusual_count += 1
            else:
                login_type = f"unknown({entry.LoginType})"
            
            entries.append({
                "login_type": login_type,
                "last_login": format_timestamp(entry.LastLogin),
                "extra": entry.Extra,
                "device_model": entry.DeviceModel,
                "device_architecture": entry.DeviceArchitecture
            })
        
        logger.info(f"✅ Successfully fetched {len(entries)} login entries for {nickname}")
        
        return {
            "success": True,
            "account": {
                "nickname": nickname,
                "account_id": account_id,
                "region": region,
                "jwt_payload": jwt_payload
            },
            "login_history": {
                "total_entries": len(entries),
                "usual_logins": usual_count,
                "unusual_logins": unusual_count,
                "entries": entries
            },
            "api_info": CHANNEL_INFO
        }
        
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout - Free Fire API not responding"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error - Check your internet"}
    except Exception as e:
        logger.error(f"Error fetching login history: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc() if app.debug else None
        }

# ============================================
# 🌐 FLASK API ENDPOINTS
# ============================================

@app.route('/', methods=['GET'])
def home():
    """API Home - Documentation & Info"""
    return jsonify({
        "api_name": "Free Fire Login History API",
        "version": "3.0.0-production",
        "developer": CHANNEL_INFO,
        "status": "online" if PROTOBUF_AVAILABLE else "degraded",
        "endpoints": {
            "GET /": "API Documentation",
            "POST /decode": "Decode JWT token and get profile info",
            "POST /history": "Get login history only",
            "POST /all": "Get both profile and complete login history",
            "GET /health": "Health check endpoint"
        },
        "usage_example": {
            "curl": "curl -X POST YOUR_DOMAIN/all -H 'Content-Type: application/json' -d '{\"token\":\"YOUR_JWT\"}'",
            "python": "import requests; requests.post('YOUR_DOMAIN/all', json={'token':'YOUR_JWT'}).json()"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "protobuf_available": PROTOBUF_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "uptime": "operational"
    })

@app.route('/ping', methods=['GET'])
def ping():
    """Legacy ping endpoint"""
    return health()

@app.route('/decode', methods=['POST'])
def decode_token():
    """Decode JWT token and return profile information"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                "success": False,
                "error": "Token is required in JSON body",
                "example": {"token": "YOUR_JWT_HERE"}
            }), 400
        
        token = data['token']
        payload = decode_jwt(token)
        
        if 'error' in payload:
            return jsonify({
                "success": False,
                "error": payload['error']
            }), 400
        
        return jsonify({
            "success": True,
            "profile": {
                "nickname": payload.get('nickname', 'N/A'),
                "account_id": payload.get('account_id', 'N/A'),
                "region": payload.get('lock_region') or payload.get('region', 'N/A'),
                "full_payload": payload
            },
            "api_info": CHANNEL_INFO
        })
        
    except Exception as e:
        logger.error(f"Decode endpoint error: {e}")
        return jsonify({
            "success": False,
            "error": "Invalid JSON body or server error"
        }), 500

@app.route('/history', methods=['POST'])
def get_history():
    """Get login history only"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                "success": False,
                "error": "Token is required"
            }), 400
        
        result = fetch_login_history(data['token'])
        
        if result['success']:
            return jsonify({
                "success": True,
                "login_history": result['login_history'],
                "api_info": CHANNEL_INFO
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"History endpoint error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/all', methods=['POST'])
def get_all():
    """Get complete data - Profile + Login History"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                "success": False,
                "error": "Token is required",
                "example": {"token": "YOUR_JWT_HERE"}
            }), 400
        
        result = fetch_login_history(data['token'])
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"All endpoint error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============================================
# 🚦 ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/health", "/ping", "/decode", "/history", "/all"]
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "success": False,
        "error": "Method not allowed"
    }), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

# ============================================
# 🚀 PRODUCTION SERVER RUNNER
# ============================================

if __name__ == '__main__':
    # Get port from environment variable (for Render/Vercel)
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    logger.info(f"{Colors.GREEN}Free Fire Login History API - Production Mode{Colors.RESET}")
    logger.info(f"{Colors.YELLOW}Developer: {CHANNEL_INFO['developer']}{Colors.RESET}")
    logger.info(f"{Colors.MAGENTA}Port: {port}{Colors.RESET}")
    logger.info(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,  # Always False in production
        threaded=True
    )