# `nginx_gzip`

Used to configure global GZIP parameters.

```yaml
nginx_gzip:
  enabled: false
  options:
    gzip_static: true
    gzip_vary: true
    gzip_proxied: any
    gzip_comp_level: 6
    gzip_min_length: 512
    gzip_buffers: 16 8k
    gzip_http_version: 1.1
    gzip_types:
      - application/javascript
      - application/x-javascript
      - image/svg+xml
      - image/x-icon
      - text/css
      - text/javascript
      - text/plain
      - text/richtext
      - text/x-component
      - text/x-js
      - text/xml
      - text/xsd
      - text/xsl
```
