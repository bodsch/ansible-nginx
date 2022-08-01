# `nginx_http`

Configures the `http {}` block of the nginx.

Via `extra_options` it is possible to integrate own extensions "hands-free".


```yaml
nginx_http:
  mime_file_path: "{{ nginx_mime_file_path }}"
  server_names_hash_bucket_size: 64
  client_max_body_size: "64m"
  access_log: "{{ nginx_logging.base_directory }}/access.log main buffer=32k flush=2m"
  sendfile: true
  tcp_nopush: true
  tcp_nodelay: true
  server_tokens: false
  rewrite_log: true
  keepalive:
    timeout: 65
    requests: 100
  proxy:
    cache_path: ''
  extra_options: {}
```

## `extra_options`

```yaml
nginx_http:

  extra_options: |
    types_hash_max_size    1024;
    types_hash_bucket_size 512;

    map_hash_max_size      128;
    map_hash_bucket_size   128;

    map $http_user_agent $excluded_ua {
      # ~Googlebot        0;
      ~monitoring-plugin 0;
      default            1;
    }

    map $remote_addr $ip_anonym {
       "~(?P<ip>(\d+)\.(\d+))\.\d+\.\d+" $ip;
       "~(?P<ip>[^:]+:[^:]+):"           $ip;
       default 0.0;
    }

    map $remote_addr $remote_addr_anon {
      ~(?P<ip>\d+\.\d+)\.         $ip.0.0;
      ~(?P<ip>[^:]+:[^:]+):       $ip::;
      default                     0.0.0.0;
    }
```