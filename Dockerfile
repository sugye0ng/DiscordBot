FROM python:3.8.5
COPY requirements.txt /tmp/
WORKDIR /tmp/
RUN pip3 install -r requirements.txt
COPY main.py /tmp/
ENV PYTHONUNBUFFERED=1
CMD ["python3", "main.py"]
