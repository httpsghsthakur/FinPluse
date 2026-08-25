import re

with open(r'README.md', 'r', encoding='utf-8') as f:
    text = f.read()

badges_old = '''![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)'''

badges_new = '''[![CI/CD Pipeline](https://img.shields.io/github/actions/workflow/status/httpsghsthakur/Finpluse/ci.yml?branch=main&label=CI%2FCD&style=for-the-badge&logo=githubactions)](https://github.com/httpsghsthakur/Finpluse/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-GHCR-blue?style=for-the-badge&logo=docker)](https://github.com/httpsghsthakur/Finpluse/pkgs/container/finpluse)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)'''

text = text.replace(badges_old, badges_new)

with open(r'README.md', 'w', encoding='utf-8') as f:
    f.write(text)
