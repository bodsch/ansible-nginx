# `nginx_custom_includes`

With `nginx_custom_includes` it is possible to store a freely definable file under `/etc/nginx/includes.d` 
to be able to use it later (e.g. in the VHost definitions).

In this way, for example, a BasicAuth configuration can be stored in a central location.

```yaml
nginx_custom_includes:
  basic_auth.conf: |
    auth_basic           "Administrator’s Area";
    auth_basic_user_file "{{ htpasswd_credentials_path }}/ba.passwdfile";
```
