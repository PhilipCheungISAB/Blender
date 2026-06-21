import socket
import json
import sys

def send_command(cmd_type, params=None):
    if params is None:
        params = {}
    
    payload = {
        "type": cmd_type,
        "params": params
    }
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)  # 2 seconds timeout to prevent hanging
        s.connect(('localhost', 9876))
        s.sendall(json.dumps(payload).encode('utf-8'))
        
        # Read response
        response_data = s.recv(65536)
        s.close()
        return json.loads(response_data.decode('utf-8'))
    except socket.timeout:
        return {"status": "error", "message": "Socket connection timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_blender_cmd.py <cmd_type> [json_params]")
        sys.exit(1)
        
    cmd_type = sys.argv[1]
    params = {}
    if len(sys.argv) >= 3:
        params = json.loads(sys.argv[2])
        
    res = send_command(cmd_type, params)
    print(json.dumps(res, indent=2))
