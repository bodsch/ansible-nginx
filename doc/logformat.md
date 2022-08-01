# `nginx_logformat`

`nginx_logformat` helps to create and manage own log formats.

For example, it is possible to change the logging completely to a json format.

```yaml
nginx_logformat:
  main:
    format: |
      '$remote_addr -
      $remote_user [$time_local] "$request" '
      '$status $body_bytes_sent "$http_referer" '
      '"$http_user_agent" "$http_x_forwarded_for"';

  json:
    format: |
      '{'
        '"time_local": "$time_local",'
        '"remote_addr": "$remote_addr",'
        '"remote_user": "$remote_user",'
        '"request": "$request",'
        '"status": "$status",'
        '"body_bytes_sent": "$body_bytes_sent",'
        '"request_time": "$request_time",'
        '"http_referrer": "$http_referer",'
        '"http_user_agent": "$http_user_agent"'
      '}';
```
