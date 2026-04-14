#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║                    FREE FIRE LOGIN HISTORY API                ║
║                                                              ║
║  📢 MAIN CHANNEL : @mahfuj_offcial                           ║
║  🔌 API CHANNEL  : @mafuapis                                 ║
║  👨‍💻 DEVELOPER    : @mahfuj_offcial_143                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
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

# --- Terminal Colors for Pretty Console Output ---
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLOR = True
except ImportError:
    COLOR = False
    class Fore:
        RED = GREEN = CYAN = YELLOW = MAGENTA = BLUE = WHITE = RESET = ''
    class Back:
        BLACK = RESET = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''

# --- Try CFONTS for Banner ---
try:
    from cfonts import render, say
    CFONTS = True
except ImportError:
    CFONTS = False

# --- Protobuf Module Import ---
try:
    import LoginHistory_pb2
except ImportError:
    print(f"{Fore.RED}❌ LoginHistory_pb2.py not found! Please keep it in the same directory.{Fore.RESET}")
    sys.exit(1)

# --- Flask Setup ---
app = Flask(__name__)
CORS(app)  # Enable CORS

# --- Channel & Developer Info ---
CHANNEL_INFO = {
    "main_channel": "@mahfuj_offcial",
    "api_channel": "@mafuapis",
    "developer": "@mahfuj_offcial_143"
}

# --- Secret Key for Decryption ---
SECRET_KEY = b"1e5898ccb8dfdd921f9bdea848768b64a201"

# ============================================
# 🎨 BANNER PRINT FUNCTION
# ============================================

def print_startup_banner():
    """Display beautiful banner on server startup"""
    
    print("\n" + "="*70)
    
    if CFONTS:
        try:
            banner = render('MAHFUJ API', font='block', gradient=['cyan', 'blue'])
            print(banner)
        except:
            pass
    
    print(f"""
{Fore.CYAN if COLOR else ''}╔══════════════════════════════════════════════════════════════╗
║                    {Fore.YELLOW if COLOR else ''}FREE FIRE LOGIN HISTORY API{Fore.CYAN if COLOR else ''}                ║
║                                                              ║
║  {Fore.GREEN if COLOR else ''}📢 MAIN CHANNEL : {Fore.WHITE if COLOR else ''}@mahfuj_offcial{Fore.CYAN if COLOR else ''}                           ║
║  {Fore.GREEN if COLOR else ''}🔌 API CHANNEL  : {Fore.WHITE if COLOR else ''}@mafuapis{Fore.CYAN if COLOR else ''}                                 ║
║  {Fore.GREEN if COLOR else ''}👨‍💻 DEVELOPER    : {Fore.WHITE if COLOR else ''}@mahfuj_offcial_143{Fore.CYAN if COLOR else ''}                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Fore.RESET if COLOR else ''}
    """)
    
    print(f"{Fore.MAGENTA if COLOR else ''}🌐 Server running at: {Fore.GREEN if COLOR else ''}http://127.0.0.1:5000{Fore.RESET if COLOR else ''}")
    print(f"{Fore.MAGENTA if COLOR else ''}📡 Public access: {Fore.GREEN if COLOR else ''}http://0.0.0.0:5000{Fore.RESET if COLOR else ''}")
    print("="*70 + "\n")

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
        return f"[DECODE_ERROR: {e}]"

def decode_jwt(token: str) -> dict:
    """Decode JWT token and extract profile data"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}
        
        payload_b64 = parts[1]
        payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        
        if 'nickname' in payload and isinstance(payload['nickname'], str):
            payload['nickname'] = decode_nickname(payload['nickname'])
        
        return payload
    except Exception as e:
        return {"error": str(e)}

def get_base_url(region: str) -> str:
    """Get API base domain by region code"""
    r = region.upper()
    if r == 'IND':
        return 'client.ind.freefiremobile.com'
    elif r in ['BR', 'US', 'NA', 'SAC']:
        return 'client.us.freefiremobile.com'
    else:
        return 'clientbp.ggpolarbear.com'

def format_timestamp(ts) -> dict:
    """Convert Unix timestamp to readable formats"""
    try:
        dt = datetime.fromtimestamp(ts)
        return {
            "timestamp": ts,
            "datetime": dt.strftime('%Y-%m-%d %H:%M:%S'),
            "date": dt.strftime('%Y-%m-%d'),
            "time": dt.strftime('%H:%M:%S'),
            "day": dt.strftime('%A'),
            "iso": dt.isoformat()
        }
    except Exception:
        return {"timestamp": ts, "error": "Invalid timestamp"}

def fetch_login_history(token: str) -> dict:
    """Main function to fetch and parse login history from Free Fire API"""
    
    # Step 1: Decode JWT
    jwt_payload = decode_jwt(token)
    if 'error' in jwt_payload:
        return {"success": False, "error": jwt_payload['error']}
    
    nickname = jwt_payload.get('nickname', 'N/A')
    account_id = jwt_payload.get('account_id', 'N/A')
    region = jwt_payload.get('lock_region') or jwt_payload.get('region')
    
    if not region:
        return {"success": False, "error": "Region not found in token"}
    
    # Step 2: Prepare API Request
    base_domain = get_base_url(region)
    url = f"https://{base_domain}/GetLoginHistory"
    
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; V2065A Build/QP1A.190711.020)',
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
            if entry.LoginType in [LoginHistory_pb2.USUAL, LoginHistory_pb2.USUAL_LOGIN]:
                login_type = "usual"
                usual_count += 1
            elif entry.LoginType in [LoginHistory_pb2.UNUSUAL, LoginHistory_pb2.UNUSUAL_LOGIN]:
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
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# ============================================
# 🌐 FLASK API ENDPOINTS
# ============================================

@app.route('/', methods=['GET'])
def home():
    """API Home - Documentation & Info"""
    return jsonify({
        "api_name": "Free Fire Login History API",
        "version": "2.0.0",
        "developer": CHANNEL_INFO,
        "status": "online",
        "endpoints": {
            "GET /": "API Documentation (this page)",
            "POST /decode": "Decode JWT token and get profile info",
            "POST /history": "Get login history only",
            "POST /all": "Get both profile and complete login history",
            "GET /ping": "Check API status"
        },
        "usage_example": {
            "curl": "curl -X POST http://127.0.0.1:5000/all -H 'Content-Type: application/json' -d '{\"token\":\"YOUR_JWT\"}'",
            "python": "import requests; requests.post('http://127.0.0.1:5000/all', json={'token':'YOUR_JWT'}).json()"
        }
    })

@app.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return jsonify({
        "status": "pong",
        "timestamp": datetime.now().isoformat(),
        "api": "online",
        "developer": CHANNEL_INFO['developer']
    })

@app.route('/decode', methods=['POST'])
def decode_token():
    """Decode JWT token and return profile information"""
    try:
        data = request.get_json()
        
        # Check if token provided
        if not data or 'token' not in data:
            return jsonify({
                "success": False,
                "error": "Token is required",
                "developer": CHANNEL_INFO['developer']
            }), 400
        
        token = data['token']
        payload = decode_jwt(token)
        
        if 'error' in payload:
            return jsonify({
                "success": False,
                "error": payload['error'],
                "developer": CHANNEL_INFO['developer']
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
        return jsonify({
            "success": False,
            "error": str(e),
            "developer": CHANNEL_INFO['developer']
        }), 500

@app.route('/history', methods=['POST'])
def get_history():
    """Get login history only"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({
                "success": False,
                "error": "Token is required",
                "developer": CHANNEL_INFO['developer']
            }), 400
        
        result = fetch_login_history(data['token'])
        
        if result['success']:
            return jsonify({
                "success": True,
                "login_history": result['login_history'],
                "api_info": CHANNEL_INFO
            })
        else:
            return jsonify({
                "success": False,
                "error": result['error'],
                "developer": CHANNEL_INFO['developer']
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "developer": CHANNEL_INFO['developer']
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
                "developer": CHANNEL_INFO['developer']
            }), 400
        
        result = fetch_login_history(data['token'])
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": result['error'],
                "developer": CHANNEL_INFO['developer']
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "developer": CHANNEL_INFO['developer']
        }), 500

# ============================================
# 🚦 ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/ping", "/decode", "/history", "/all"],
        "developer": CHANNEL_INFO['developer']
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "developer": CHANNEL_INFO['developer']
    }), 405

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "developer": CHANNEL_INFO['developer']
    }), 500

# ============================================
# 🚀 SERVER RUNNER
# ============================================

if __name__ == '__main__':
    # Print beautiful startup banner
    print_startup_banner()
    
    # Log startup
    print(f"{Fore.GREEN if COLOR else ''}✅ API Server Started Successfully!{Fore.RESET if COLOR else ''}")
    print(f"{Fore.YELLOW if COLOR else ''}📝 Logs will appear below:{Fore.RESET if COLOR else ''}")
    print("-" * 70)
    
    # Run Flask app
    app.run(
        host='0.0.0.0',  # Listen on all interfaces
        port=5000,        # Default port
        debug=True,       # Debug mode ON (shows errors)
        threaded=True     # Handle multiple requests
    )