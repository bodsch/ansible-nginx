
# Ansible Role:  `nginx`

Ansible role to install and configure nginx.


[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/bodsch/ansible-nginx/CI)][ci]
[![GitHub issues](https://img.shields.io/github/issues/bodsch/ansible-nginx)][issues]
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/bodsch/ansible-nginx)][releases]

[ci]: https://github.com/bodsch/ansible-nginx/actions
[issues]: https://github.com/bodsch/ansible-nginx/issues?q=is%3Aopen+is%3Aissue
[releases]: https://github.com/bodsch/ansible-nginx/releases


## Requirements & Dependencies

- None

### Operating systems

Tested on

* ArchLinux
* ArtixLinux
* Debian based
    - Debian 11
    - Ubuntu 20.10


## usage

### default configuration

```yaml
nginx_acme: {}

nginx_default_site:
  file: /etc/nginx/sites-enabled/default
  remove: true

nginx_vhost_templates:
  http: vhost_http.conf.j2
  https: vhost_https.conf.j2
  redirect: vhost_redirect.conf.j2

nginx_logging:
  base_directory: /var/log/nginx

nginx_global: {}

nginx_events:
  worker_connections: "1024"
  multi_accept: false

nginx_logformat: {}

nginx_http: {}

nginx_gzip: {}

nginx_ssl: {}

nginx_custom_includes: {}

nginx_includes:
  - "/etc/nginx/conf.d/*.conf"
  - "/etc/nginx/sites-enabled/*.conf"

nginx_vhosts: {}
```

- [`nginx_acme`](doc/acme.md)
- [`nginx_custom_includes`](doc/custom_includes.md)
- [`nginx_global`](doc/global.md)
- [`nginx_gzip`](doc/gzip.md)
- [`nginx_http`](doc/http.md)
- [`nginx_logformat`](doc/logformat.md)
- [`nginx_ssl`](doc/ssl.md)
- [`nginx_vhosts`](doc/vhosts.md)


## Contribution

Please read [Contribution](CONTRIBUTING.md)

## Development,  Branches (Git Tags)

The `master` Branch is my *Working Horse* includes the "latest, hot shit" and can be complete broken!

If you want to use something stable, please use a [Tagged Version](https://github.com/bodsch/ansible-nginx/-/tags)!

---

## Author and License

- Bodo Schulz

## License

[Apache](LICENSE)

**FREE SOFTWARE, HELL YEAH!**
