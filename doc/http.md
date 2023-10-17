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
  resolver:
    resolvers: []
    timeout: ""
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
    cache_path: []                                        #
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
```

## `proxy.cache_path`

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
```

## `extra_options`

Via `extra_options` it is possible to integrate own extensions "hands-free".

```yaml
nginx_http:

  extra_options: |
    satisfy any;
    directio 10m;
```
