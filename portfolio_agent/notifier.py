from pushbullet import Pushbullet
from portfolio_agent.config import PUSHBULLET_API_KEY

pb = Pushbullet(PUSHBULLET_API_KEY)

def push(text: str):
    pb.push_note(title="Portfolio Assistant", body=text)