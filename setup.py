from setuptools import setup

setup(
    name="spacesaver",
    version="0.1.0",
    description="A directory size analysis tool with GUI",
    author="SpaceSaver Developer",
    py_modules=["spacesaver"],
    install_requires=[
        "matplotlib",
    ],
    entry_points={
        "console_scripts": [
            "spacesaver=spacesaver:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)