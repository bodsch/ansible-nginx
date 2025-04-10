# `nginx_global`

Configures the global section of the nginx.

Via the dictionary `extra_options` it is possible to integrate own extensions "hands-free".


```yaml
nginx_global:
  # https://nginx.org/en/docs/ngx_core_module.html
  daemon: ""                  # true
  debug_points: ""            #
  env: []                     #
  error_log: "{{ nginx_logging.base_directory }}/error.log warn"
  include_modules: true
  includes: []                #
  load_modules: []            #
  lock_file: ""               # logs/nginx.lock
  master_process: ""          # true
  pcre_jit: ""                # false
  pid: ""                     # logs/nginx.pid
  ssl_engine: ""              #
  thread_pool: {}             # default: { threads=32, max_queue=65536 }
  timer_resolution: ""        #
  worker_processes: "auto"    # {{ ansible_processor_vcpus | default(ansible_processor_count) }}"
  worker_cpu_affinity:  ""    # auto [cpumask]
  worker_priority: ""         # 0
  worker_rlimit_core: ""      #
  worker_rlimit_nofile: ""    #
  worker_shutdown_timeout: "" #
  working_directory: ""       #
  extra_config: {}
```

### `nginx_global.extra_config`

Via `extra_options` it is possible to integrate own extensions "hands-free".

```yaml
nginx_global:

  extra_config: ""

```
