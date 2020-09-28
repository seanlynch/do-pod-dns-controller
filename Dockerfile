FROM python:3.8-slim
RUN addgroup --gid 1000 controller
RUN adduser --uid 1000 --gid 1000 --disabled-password controller --gecos 'do-pod-dns-controller' --home /home/controller
USER controller:controller
WORKDIR /home/controller
RUN python3 -m pip install --user virtualenv
RUN python3 -m venv env
ADD --chown=controller:controller ./ /home/controller/src
RUN . /home/controller/env/bin/activate && pip install wheel
RUN . /home/controller/env/bin/activate && pip install ./src
RUN rm -rf src
ENTRYPOINT ["/home/controller/env/bin/do-pod-dns-controller"]
