FROM python:3.12
RUN <<EOF
cd /usr/src
pip install . 
EOF
ENTRYPOINT [ "/usr/local/bin/uwsgi", "--http", ":9090", "--wsgi-file", "/usr/local/bin/manager.py" ]