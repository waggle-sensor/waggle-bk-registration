FROM ubuntu:20.04

# for testing
RUN apt-get update && apt-get install --no-install-recommends -y \
  python3 \
  python3-click
  #python3-pip

# for testing
#COPY requirements.txt .
#RUN pip3 install -r requirements.txt

COPY . /workdir
WORKDIR /workdir
