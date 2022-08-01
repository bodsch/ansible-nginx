# `nginx_global`

Configures the global section of the nginx.

Via the dictionary `extra_options` it is possible to integrate own extensions "hands-free".



```yaml
nginx_global:
  error_log: "{{ nginx_logging.base_directory }}/error.log warn"
  worker_processes: "{{ ansible_processor_vcpus | default(ansible_processor_count) }}"
  include_modules: true
  extra_config: {}
```

### `nginx_global.extra_config`

```yaml
nginx_global:

  extra_config:

```
