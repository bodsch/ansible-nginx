# `nginx_ssl`

Used to configure global SSL parameters.

```yaml
nginx_ssl:
  enabled: true
  ssl_session_timeout: 5m
  # Enable all TLS versions (TLSv1.3 is required for QUIC).
  ssl_protocols:
    - TLSv1.1
    - TLSv1.2
    - TLSv1.3
  ssl_ciphers:
    my_own_ciphers:
      - EECDH+AESGCM
      - EDH+AESGCM
      - AES256+EECDH
      - AES256+EDH
  ssl_prefer_server_ciphers: true
  ssl_session_cache: shared:SSL:10m
```


