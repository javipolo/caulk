FROM python:3.9
LABEL mantainer=javipolo@drslump.org

WORKDIR /src

COPY requirements.txt caulk.py common.py /src
RUN pip install -r requirements.txt

CMD [ "kopf", "run", "/src/caulk.py" ]
