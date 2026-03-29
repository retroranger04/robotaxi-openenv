from openenv import create_fastapi_app
from env.environment import RobotaxiEnv

env = RobotaxiEnv()
app = create_fastapi_app(env)
