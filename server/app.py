from env import create_fastapi_app, RobotaxiEnv


def main():
    env = RobotaxiEnv()
    app = create_fastapi_app(env)
    return app


if __name__ == "__main__":
    main()
