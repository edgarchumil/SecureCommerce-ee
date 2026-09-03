FROM alpine:3.21

RUN apk add --no-cache postgresql17-client openssl tzdata
COPY backup.sh restore.sh verify.sh /usr/local/bin/
RUN chmod 0555 /usr/local/bin/backup.sh /usr/local/bin/restore.sh /usr/local/bin/verify.sh

ENTRYPOINT ["/usr/local/bin/backup.sh"]
