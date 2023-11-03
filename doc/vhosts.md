# `nginx_vhosts`

The central place to manage VHosts.

`nginx_vhosts` is designed as a dictionary.

This means that each entry is unique, but can be redefined via a `combine()`.

A simple example:

```yaml
nginx_vhosts:

  - name: nginx-status
    filename: 00-status
    state: present  # default: present
    enabled: true   # default: true

    # a list of domain(s)
    domains:
      - localhost

    # listen
    listen: 127.0.0.1:8088

    # locations
    locations:
      "/nginx_status":
        options: |
          stub_status on;
          access_log off;
          allow 127.0.0.1;
          deny all;
```

## `state` / `enabled`

Each VHost definition created (with a `state` of `present`) is created under `/etc/nginx/sites-available`.
Only when `enabled` is defined with `true` will this VHost file be linked to `/etc/nginx/sites-enabled`.

In this way, VHost definitions can also be deactivated or removed.

## `filename`

If `filename` is not defined, the identifier of the dictionary is automatically chosen as the file name.

## `domains`

If a VHost is to handle several domains, these can be entered under `domains`.

## `listen`

If several listeners per VHost are desired, `listen` can be defined as a list instead of a string:

```yaml
nginx_vhosts:

  - name: bar.molecule.lan
    ...

    listen:
      - "9000"
      - "[::]:9000 ipv6only=on"

    ...
```

## `logfiles`

Individual log files are created for each VHost.
If these are not explicitly configured, a few log files for access and error messages are defined under `/var/log/nginx`.

This then corresponds to the following scheme:
`/var/log/nginx/$key_access.log` or `/var/log/nginx/$key_error.log`.

Own definitions can be made via the parameter `logfiles`:

```yaml
nginx_vhosts:

  - name: bar.molecule.lan
    ...

    logfiles:
      access:
        file: /var/log/nginx/bar.molecule.lan/access.log
        loglevel: json
      error:
        file: /var/log/nginx/bar.molecule.lan/error.log
        loglevel: notice

    ...
```

The appropriate log format can be selected via the `loglevel` parameter.

Available log levels:

| Loglevel   | Description |
| :------    | :-----      |
| `Debug`    | Debugging messages that are not useful most of the time.             |
| `Info`     | Informational messages that might be good to know.                   |
| `Notice`   | Something normal but significant happened and it should be noted.    |
| `Warn`     | Something unexpected happened, however it’s not a cause for concern. |
| `Error`    | Something failed.                                                    |
| `Crit`     | A critical condition occurred.                                       |
| `Alert`    | Immediate action is required.                                        |
| `Emerg`    | The system is unusable.                                              |


If this is not defined, the nginx default is selected.

### `syslog`

A syslog server can also be defined as a log endpoint.

> **The corresponding log server (syslog-ng, rsyslog, loki) must provide a UDP port for this!**

A detailed documentation about the syslog integration can be found directly at [Nginx](https://nginx.org/en/docs/syslog.html).

A corresponding configuration could - for example - look like this:

```yaml
nginx_vhosts:

  - name: bar.molecule.lan
    ...

    logfiles:
      access:
        syslog:
          server: 127.0.0.1:514
          # facility=string
          # severity=string
          # tag=string
          options:
            - facility=local0
            - tag=nginx
            - severity=debug
        loglevel: 'json_combined'
      error:
        syslog:
          server: 127.0.0.1:514
        loglevel: notice

    ...
```

## `locations`

Each VHost definition can contain several locations.

These are freely definable and are defined as a text block:

```yaml
nginx_vhosts:

  - name: bar.molecule.lan
    ...

    locations:
      "^~ /":
        options: |
          add_header X-Backend "bar";

          proxy_pass         http://paperless/;
          proxy_set_header   Host              $host;
          proxy_set_header   X-Real-IP         $remote_addr;
          proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
          proxy_set_header   X-Forwarded-Proto $scheme;

    ...
```

This configuration would create the following nginx location:

```bash
  location ^~ / {
    add_header X-Backend "bar";

    proxy_pass         http://paperless/;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Real-IP         $remote_addr;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;

  }
```

## `upstreams`

If you are configuring Nginx as a load balancer, you can define one or more upstream sets using this variable.

In addition to defining at least one upstream, you would need to configure one of your server blocks to proxy requests through the defined upstream (e.g. `proxy_pass http://paperless/;`)

```yaml
nginx_vhosts:

  - name: bar.molecule.lan
    ...

    upstreams:
      - name: paperless
        servers:
          - 127.0.0.1:8080   max_fails=3 fail_timeout=30s
        # strategy: 'ip_hash'
        keepalive: 32

    ...
```

## `ssl`

Managing TLS VHost Definition is a little trickier.

Corresponding certificates can be defined via `ssl`:

```yaml
nginx_vhosts:

  - name: bar.molecule.lan
    ...

    ssl:
      enabled: true
      ciphers: default
      certificate: /etc/letsencrypt/live/bar.molecule.lan/fullchain.pem
      certificate_key: /etc/letsencrypt/live/bar.molecule.lan/privkey.pem
    ...
```

The keyword `ciphers` can be used to define an individual configuration file with ciphers.

These can be defined via `nginx_ssl.ssl_ciphers`.

**However, nginx would not start if the certificates are not available!**

Therefore, these VHost definitions are only activated when the corresponding certificates are available in the system.

It is also possible to trigger a corresponding ACME challenge at Let's Encrypt with this role, have the certificates
deposited in the system and then activate the TLS VHosts definition.


## `redirect`

A redirect from port 80 (or any other port) to a TLS vhost can be defined via `redirect`:


```yaml
nginx_vhosts:

  - name: bar.molecule.lan
    ...

    redirect:
      from_port: 80
    ...
```


## Complete example

```yaml
nginx_vhosts:

  - name: nginx-status
    state: present
    enabled: true

    filename: 00-status

    domains:
      - localhost

    listen: 127.0.0.1:8088

    locations:
      "/nginx_status":
        options: |
          stub_status on;
          access_log off;
          allow 127.0.0.1;
          deny all;


  - name: 10-prometheus.molecule.lan
    state: present
    enabled: false

    domains:
      - prometheus.molecule.lan

    listen: 80

    root_directory:  /var/www/prometheus.molecule.lan
    root_directory_create: true

    logfiles:
      access:
        file: /var/log/nginx/prometheus.molecule.lan/access.log
        loglevel: json
      error:
        file: /var/log/nginx/prometheus.molecule.lan/error.log
        loglevel: notice

    upstreams:
      - name: prometheus
        servers:
          - 127.0.0.1:9090   max_fails=3 fail_timeout=30s
        keepalive: 32

    locations:
      "^~ /":
        options: |
          add_header X-Backend "prometheus";

          proxy_pass         http://prometheus/;
          proxy_set_header   Host              $host;
          proxy_set_header   X-Real-IP         $remote_addr;
          proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
          proxy_set_header   X-Forwarded-Proto $scheme;


  - name: 20-bar.molecule.lan
    state: absent
    enabled: true

    domains:
      - bar.molecule.lan
      - ruf.molecule.lan
      - slo.molecule.lan
      - zup.molecule.lan

    redirect:
      from_port: 80

    listen:
      - 8443 reuseport
      - 443 ssl http2

    logfiles:
      access:
        syslog:
          server: 127.0.0.1:514
          options:
            - facility=local0
            - tag=nginx
            - severity=debug
        loglevel: 'json_combined'
      error:
        syslog:
          server: 127.0.0.1:514
        loglevel: notice

    ssl:
      enabled: true
      certificate: /etc/ssl/certs/ssl-cert-snakeoil.pem
      certificate_key: /etc/ssl/private/ssl-cert-snakeoil.key
```
