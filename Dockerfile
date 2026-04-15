FROM python:3.12
COPY . /usr/src
COPY docs/samm-update-credentials.html /app/samm-update-credentials.html
RUN <<EOF
cd /usr/src
pip install multipart python-multipart
pip install --force-reinstall git+https://github.com/samanamonitor/pysammmanager.git
EOF
ENTRYPOINT [ "/usr/local/bin/uwsgi", "--http", ":9090", "--wsgi-file", "/usr/local/bin/manager.py" ]
