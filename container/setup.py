from setuptools import setup, find_packages

setup(
    name="buddha-py",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "python-dotenv",
        "weaviate-client",
        "openai",
        "langchain",
        "langchain-openai",
        "langchain-experimental",
        "pypdf",
        "PyJWT",
        "werkzeug",
    ],
    python_requires=">=3.8",
) 