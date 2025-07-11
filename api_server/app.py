from fastapi import FastAPI, Request, Header, HTTPException
import yaml
import central_engine.dispatcher as dispatcher
import central_engine.rule_logger as rule_logger
from central_engine.trigger_engine import is_quarantined

with open('central_engine/config.yaml') as f:
    config = yaml.safe_load(f)
API_KEY = config.get('api_key', 'changeme')

app = FastAPI()

@app.post('/push-rule')
async def push_rule(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')
    data = await request.json()
    src_ip = data.get('metadata', {}).get('source_ip')
    if src_ip and is_quarantined(src_ip):
        # Only allow explicit allow rules (future work)
        return {'status': 'blocked', 'response': f'Agent {src_ip} is quarantined. Rule push not allowed.'}
    status, resp = dispatcher.dispatch_rule(data)
    return {'status': status, 'response': resp}

@app.post('/ack')
async def ack(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')
    data = await request.json()
    rule_logger.log_rule(data)
    return {'status': 'logged'} 