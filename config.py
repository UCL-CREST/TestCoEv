import os

PROJECT_PATH = os.path.dirname(__file__)
OUTPUT_PATH = f"{PROJECT_PATH}/.tmp"
JAVA_PATH = f'{os.environ["JAVA_HOME"]}/bin' if "JAVA_HOME" in os.environ else None
GUMTREE_PATH = f"{PROJECT_PATH}/libs/gumtree/bin"
