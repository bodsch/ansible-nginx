# `nginx_upstreams`

gloabl definition:

```yaml
nginx_upstreams:
  - name: grafana
    # description: upstream  to local grafana
    servers:
      - 127.0.0.1:3000
  - name: prometheus
    # description: upstream  to local prometheus
    servers:
      - 127.0.0.1:9090
```

or vhost based:

```yaml
nginx_vhosts:

  - name: 25-git.matrix.lan
    description: |
      internal access to http://git.matrix.lan
    filename: 25-git.matrix.lan.conf

    domains:
      - git.matrix.lan

    listen:
      - 80

    upstreams:
      - name: git
        servers:
          - 192.168.0.135:3000

```
