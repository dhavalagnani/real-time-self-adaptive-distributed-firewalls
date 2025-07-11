import time
import re
from utils.constants import DEFAULT_RULE_FORMAT
from utils.helpers import validate_rule

def is_valid_ip(ip):
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    if not re.match(pattern, ip):
        return False
    return all(0 <= int(part) <= 255 for part in ip.split('.'))

def is_valid_port(port):
    return isinstance(port, int) and 1 <= port <= 65535

def generate_nft_rule(anomaly_dict):
    src_ip = anomaly_dict.get('source_ip')
    dst_port = anomaly_dict.get('dest_port')
    attack_type = anomaly_dict.get('attack_type')
    if not (is_valid_ip(src_ip) and is_valid_port(dst_port)):
        raise ValueError('Invalid IP or port')
    rule_str = f"nft add rule inet filter input ip saddr {src_ip} tcp dport {dst_port} drop"
    metadata = {
        'source_ip': src_ip,
        'dest_port': dst_port,
        'attack_type': attack_type,
        'timestamp': int(time.time())
    }
    return {'rule_str': rule_str, 'metadata': metadata}

def map_alert_to_rule(alert):
    """Maps a high-level anomaly alert to an nftables-compatible rule string."""
    # Try to extract relevant fields
    src_ip = alert.get('source_ip')
    dest_ip = alert.get('dest_ip')
    event_type = alert.get('event_type', '')
    description = alert.get('description', '')
    # Default: block source IP
    if src_ip and is_valid_ip(src_ip):
        rule_str = f"nft add rule inet filter input ip saddr {src_ip} drop"
    else:
        rule_str = None
    # If Suricata alert with dest_port, block src_ip:dest_port
    dest_port = alert.get('dest_port') or alert.get('dest_port') or None
    if dest_port:
        try:
            port = int(dest_port)
            if is_valid_port(port) and src_ip and is_valid_ip(src_ip):
                rule_str = f"nft add rule inet filter input ip saddr {src_ip} tcp dport {port} drop"
        except Exception:
            pass
    # If Zeek beaconing, block src_ip to dest_ip
    if event_type == 'zeek_conn_alert' and src_ip and dest_ip and is_valid_ip(src_ip) and is_valid_ip(dest_ip):
        rule_str = f"nft add rule inet filter input ip saddr {src_ip} ip daddr {dest_ip} drop"
    # Metadata for traceability
    metadata = {
        'source_ip': src_ip,
        'dest_ip': dest_ip,
        'event_type': event_type,
        'description': description,
        'timestamp': int(time.time())
    }
    return {'rule_str': rule_str, 'metadata': metadata} 