# `nginx_http`

Configures the `http {}` block of the nginx.

```yaml
nginx_http:
  mime_file_path: "{{ nginx_mime_file_path }}"            #
  client:                                                 #
    max_body_size: "64m"                                  #
    body:                                                 #
      buffer_size: ""                                     #
      in_file_only: ""                                    #
      in_single_buffer: ""                                #
      temp_path: ""                                       #
      timeout: ""                                         #
    header:                                               #
      buffer_size: ""                                     #
      timeout: ""                                         #
  access_log: "{{ nginx_logging.base_directory }}/access.log main buffer=32k flush=2m"
  open_log_file_cache: ""                                 # example: 'max=1000 inactive=20s valid=1m min_uses=2'
  geoip:                                                  # https://nginx.org/en/docs/http/ngx_http_geoip_module.html
    country: ""                                           # geoip_country file;
    city: ""                                              # geoip_city file;
    org: ""                                               # geoip_org file;
    proxy: ""                                             # geoip_proxy address | CIDR;
    proxy_recursive: ""                                   # geoip_proxy_recursive on | off;  
  limits:                                                 #
    # https://nginx.org/en/docs/http/ngx_http_limit_conn_module.html
    conn:
      conn: []                                            #                  # limit_conn zone number;
      conn_status: ""                                     # 503              # limit_conn_status code;
      conn_log_level: ""                                  # error            # limit_conn_log_level info | notice | warn | error;
      conn_dry_run: ""                                    # false            # limit_conn_dry_run on | off;
      conn_zone: []                                       #                  # limit_conn_zone key zone=name:size;
      zone: ""                                            #                  # limit_zone name $variable size;
    # https://nginx.org/en/docs/http/ngx_http_limit_req_module.html
    req:                                                  #                  #
      req: []                                             #                  # limit_req zone=name [burst=number] [nodelay | delay=number];
      req_dry_run: ""                                     #                  # limit_req_dry_run on | off;
      req_log_level: ""                                   #                  # limit_req_log_level info | notice | warn | error;
      req_status: ""                                      #                  # limit_req_status code;
      req_zone: []                                        #                  # limit_req_zone key zone=name:size rate=rate [sync];  
  resolver:
    address: ""                                           # 127.0.0.1 [::1]:5353 valid=30s [ipv4=on|off] [ipv6=on|off]
    timeout: ""                                           # 5s
  sendfile: true                                          #
  tcp:
    nopush: true                                          #
    nodelay: true                                         #
  server_tokens: false                                    #
  server_name:
    in_redirect: ""                                       #
  server_names:
    hash_bucket_size: ""
    hash_max_size: ""
    in_redirect: ""
  rewrite_log: true                                       #
  keepalive:                                              #
    disable: ""                                           # Disables keep-alive connections with misbehaving browsers.
    requests: ""                                          # Sets the maximum number of requests that can be served through one keep-alive connection.
    time: ""                                              # Limits the maximum time during which requests can be processed through one keep-alive connection.
    timeout: ""                                           # The first parameter sets a timeout during which a keep-alive client connection will stay open on the server side.
  proxy:                                                  #
    bind: ""                                              #
    buffer_size: ""                                       #
    buffering: ""
    buffers: ""
    cache: ""
    cache_background_update: ""
    cache_path: []                                        #
    cache_purge: ""                                       #
    cache_revalidate: ""
    cache_use_stale: ""
    cache_methods: []                                     #
    cache_key: ""                                         #
    headers_hash:                                         #
      max_size: ""                                        #
      bucket_size: ""                                     #
    hide_header: []                                       #
    http_version: "1.1"                                   #
    ignore_client_abort: ""                               #
    ignore_headers: []                                    #
    limit_rate: ""                                        #
    set_headers: {}                                       #
  maps: []                                                #
  map_hash:                                               #
    max_size: ""                                          #
    bucket_size: ""                                       #
  types_hash:                                             #
    max_size: ""                                          # Sets the maximum size of the types hash tables
    bucket_size: ""                                       # Sets the bucket size for the types hash tables
  variables_hash:
    max_size: ""                                          # Sets the maximum size of the variables hash table.
    bucket_size: ""                                       # Sets the bucket size for the variables hash table.
  extra_options: {}                                       #
  global:
    deny: []
    allow: []
  includes:
    - "/etc/nginx/conf.d/*.conf"
    - "/etc/nginx/sites-enabled/*.conf"
```

## `resolver`

```yaml
nginx_http:

  resolver:
    address: "172.17.0.1 141.1.1.1 valid=60s" # version 1.23.1: ipv4=on ipv6=off"
    timeout: "30s"
```

## `proxy.cache_path`

[upstream doku](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache_path)

```yaml
nginx_http:

  proxy:
    cache_path:
      - path: "/var/cache/nginx/studio"
        options:
          - levels=1:2
          - keys_zone=studio_cache:10m
          - max_size=50m
          - inactive=60m
          - use_temp_path=off
      - path: /var/cache/nginx/preview
```

## `maps`

See also nginx documention for the [ngx_http_map_module](http://nginx.org/en/docs/http/ngx_http_map_module.html).

```yaml
nginx_http:

  maps:
    - name: http_user_agent
      description: matched 'http_user_agent'
      variable: excluded_ua
      mapping:
        - source: "~monitoring-plugin"
          result: 0
        - source: "default"
          result: 1

    - name: remote_addr
      description: matched against 'remote_addr' and anonymises the corresponding IPs
      variable: ip_anonym
      mapping:
        - source: !unsafe "~(?P<ip>(\\d+)\\.(\\d+))\\.\\d+\\.\\d+"
          result: "$ip"
        - source: "~(?P<ip>[^:]+:[^:]+):"
          result: "$ip"
        - source: "default"
          result: "0.0"

    - name: remote_addr
      description: matched against 'remote_addr' and anonymises the corresponding IPs
      variable: remote_addr_anon
      mapping:
        - source: "~(?P<ip>\\d+\\.\\d+)\\."
          result: "$ip.0.0"
        - source: "~(?P<ip>[^:]+:[^:]+):"
          result: "$ip::"
        - source: "default"
          result: "0.0.0.0"

    - name: http_user_agent
      description: matched against 'http_user_agent' for bad user agents
      variable: badagent
      mapping:
        - source: default
          result: 0
        - source: ~*malicious
          result: 1
        - source: ~*backdoor
          result: 1
        - source: ~*netcrawler
          result: 1
        - source: ~Antivirx
          result: 1
        - source: ~Arian
          result: 1
        - source: ~webbandit
          result: 1
        - source: ~cyberscan
          result: 1
        - source: ~*paloaltonetworks.com
          result: 1
        - source: ~Googlebot
          result: 1
        - source: ~Download Demon
          result: 1
```


## `global`

```yaml
nginx_http:

  global:
    deny:
      - description: "paoalto"
        values:
          - "205.210.31.205"
          - "162.216.149.197"
      - description: "censys"
        values:
          - "167.94.146.63"
    allow:
      - description: "localhost"
        values:
          - "127.0.1.1"
```

## `limits`

```yaml
nginx_http:

  limits:
    # https://nginx.org/en/docs/http/ngx_http_limit_conn_module.html
    conn:
      conn:
        - limit_conn_by_addr    50
        - limit_conn_by_servers 2000
      conn_status: 429
      conn_log_level: notice
      conn_dry_run: true
      conn_zone:
        - $binary_remote_addr zone=conn_limit_per_ip:10m
        - $binary_remote_addr zone=limit_conn_by_addr:20m
        - $server_name        zone=limit_conn_by_servers:10m
      zone: ""
    # https://nginx.org/en/docs/http/ngx_http_limit_req_module.html
    req:
      req:
        - zone=req_zone    burst=10 delay=15
        - zone=req_zone_wl burst=20 nodelay
      req_dry_run: true
      req_log_level: notice
      req_status: 429
      req_zone:
        - $binary_remote_addr zone=req_zone:10m     rate=10r/s
        - $binary_remote_addr zone=req_zone_wl:10m  rate=15r/s
```

## `geoip`

**ATTENTION!**

Debian (12?) no longer provides full geoip support.  
The `geoip-database-extra` package has been removed, therefore no GeoIP-City data can be provided.

As an alternative you can use my [geoip role](https://github.com/bodsch/ansible-geoip).

```yaml

nginx_extra_modules:
  - "{{ 'libnginx-mod-http-geoip' if ansible_os_family | lower == 'debian' else 'nginx-mainline-mod-geoip' }}"

nginx_http:

  # https://nginx.org/en/docs/http/ngx_http_geoip_module.html
  geoip:
    # SET the path to the .dat file used for determining the visitor's country from$
    country: "/usr/share/GeoIP/GeoIP-Country.dat"
    # SET the path to the .dat file used for determining the visitor's country from$
    city: "/usr/share/GeoIP/GeoIP-City.dat"
```

With GeoIP support you still have logging parameters available.

I have a corresponding [example configuration](https://github.com/bodsch/ansible-nginx/blob/main/molecule/configured/group_vars/all/vars.yml#L89-L97) here.

## `geoip2`

In the meantime, I have integrated geoip2 support.  
Both in the [geoip role](https://github.com/bodsch/ansible-geoip) and here in nginx.

```yaml

nginx_extra_modules:
  - "{{ 'libnginx-mod-http-geoip2' if ansible_os_family | lower == 'debian' else 'ngx_http_geoip2_module' }}"

nginx_http:

  includes:
    - includes.d/geoip2.rules

  maps:
    - name: geoip2_country_iso
      description: GeoBlock ...
      variable: allowed_country
      mapping:
        - source: IN
          result: "no"
        - source: HK
          result: "no"
        - source: US
          result: "no"
        - source: UK
          result: "no"
        - source: "default"
          result: "yes"

  geoip2:
    city:
      database: /usr/share/GeoIP/GeoLite2-City.mmdb
      auto_reload: 5m
```


## `extra_options`

Via `extra_options` it is possible to integrate own extensions "hands-free".

```yaml
nginx_http:

  extra_options: |
    satisfy any;
    directio 10m;
```
