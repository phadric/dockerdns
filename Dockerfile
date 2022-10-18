FROM alpine
RUN apk --no-cache add docker-py py3-dnspython
COPY dockerdns.py .

CMD python3 /dockerdns.py $DNSSERVER $DOMAIN
