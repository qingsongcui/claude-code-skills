from setuptools import setup, find_packages

setup(
    name="repo-distillation-preflight",
    version="0.1.0",
    description="Fast, local-first AST and license preflight tool for packaging repositories into Agent Skills.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="George O'Nair",
    author_email="a985783827@gmail.com",
    url="https://george-onair.whop.site/shop/agentic-distiller",
    project_urls={
        "Homepage": "https://george-onair.whop.site/shop/agentic-distiller",
        "Documentation": "https://george-onair.whop.site/workflows/agents",
        "Repository": "https://github.com/qingsongcui/claude-code-skills",
    },
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "repo-preflight = repo_preflight.cli:main",
        ],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
)
