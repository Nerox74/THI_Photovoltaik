FROM ubuntu:latest
LABEL authors="nilsschaftlein"

ENTRYPOINT ["top", "-b"]