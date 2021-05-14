FROM python:3.9
LABEL mantainer=javipolo@drslump.org

WORKDIR /src

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY caulk.py common.py ./

CMD [ "kopf", "run", "./caulk.py" ]
