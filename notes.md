
# before

## first run

Montag 12 Juni 2023  13:42:19 +0200 (0:00:00.634)       0:00:49.855 ***********
===============================================================================
ansible-nginx : create HTTP vhost configurations ----------------------- 21.58s
ansible-nginx : install nginx ------------------------------------------- 8.63s
ansible-nginx : create nginx sites directories -------------------------- 2.17s
ansible-nginx : update package cache ------------------------------------ 2.01s
ansible-nginx : create nginx main configuration ------------------------- 1.76s
ansible-nginx : create gzip configuration ------------------------------- 1.54s
ansible-nginx : create HTTPs vhost configurations ----------------------- 1.46s
ansible-nginx : create custom includes ---------------------------------- 1.31s
ansible-nginx : create logformat configuration -------------------------- 1.28s
ansible-nginx : reload service ------------------------------------------ 0.88s
ansible-nginx : validate config ----------------------------------------- 0.66s
ansible-nginx : create ssl configuration -------------------------------- 0.66s
ansible-nginx : ensure vhosts log path exists --------------------------- 0.64s
ansible-nginx : ensure nginx is enabled on boot ------------------------- 0.63s
ansible-nginx : find primary group for user 'www-data' ------------------ 0.63s
ansible-nginx : de-activate vhosts -------------------------------------- 0.61s
ansible-nginx : checking existing domains certificates ------------------ 0.60s
ansible-nginx : enable HTTP sites configs ------------------------------- 0.54s
ansible-nginx : remove vhost configurations ----------------------------- 0.54s
ansible-nginx : remove default site ------------------------------------- 0.53s


## second run

Montag 12 Juni 2023  13:45:03 +0200 (0:00:00.678)       0:00:35.180 ***********
===============================================================================
ansible-nginx : create HTTP vhost configurations ----------------------- 15.14s
ansible-nginx : create nginx sites directories -------------------------- 2.24s
ansible-nginx : update package cache ------------------------------------ 2.24s
ansible-nginx : create HTTPs vhost configurations ----------------------- 1.96s
ansible-nginx : install nginx ------------------------------------------- 1.64s
ansible-nginx : create nginx main configuration ------------------------- 1.00s
ansible-nginx : create gzip configuration ------------------------------- 0.99s
ansible-nginx : reload service ------------------------------------------ 0.93s
ansible-nginx : create custom includes ---------------------------------- 0.87s
ansible-nginx : create logformat configuration -------------------------- 0.86s
ansible-nginx : ensure nginx is enabled on boot ------------------------- 0.68s
ansible-nginx : validate config ----------------------------------------- 0.67s
ansible-nginx : create ssl configuration -------------------------------- 0.65s
ansible-nginx : ensure vhosts log path exists --------------------------- 0.63s
ansible-nginx : find primary group for user 'www-data' ------------------ 0.63s
ansible-nginx : de-activate vhosts -------------------------------------- 0.62s
ansible-nginx : checking existing domains certificates ------------------ 0.62s
ansible-nginx : enable HTTP sites configs ------------------------------- 0.56s
ansible-nginx : remove default site ------------------------------------- 0.56s
ansible-nginx : enable HTTPs sites configs with existing certificates --- 0.54s


## third run

Montag 12 Juni 2023  13:45:58 +0200 (0:00:00.867)       0:00:33.999 ***********
===============================================================================
ansible-nginx : create HTTP vhost configurations ----------------------- 15.12s
ansible-nginx : create nginx sites directories -------------------------- 2.47s
ansible-nginx : update package cache ------------------------------------ 2.19s
ansible-nginx : install nginx ------------------------------------------- 1.69s
ansible-nginx : create nginx main configuration ------------------------- 1.19s
ansible-nginx : create gzip configuration ------------------------------- 1.13s
ansible-nginx : create logformat configuration -------------------------- 1.00s
ansible-nginx : create custom includes ---------------------------------- 0.99s
ansible-nginx : create HTTPs vhost configurations ----------------------- 0.99s
ansible-nginx : ensure nginx is enabled on boot ------------------------- 0.87s
ansible-nginx : create ssl configuration -------------------------------- 0.76s
ansible-nginx : find primary group for user 'www-data' ------------------ 0.72s
ansible-nginx : de-activate vhosts -------------------------------------- 0.71s
ansible-nginx : ensure vhosts log path exists --------------------------- 0.68s
ansible-nginx : checking existing domains certificates ------------------ 0.67s
ansible-nginx : remove default site ------------------------------------- 0.62s
ansible-nginx : remove vhost configurations ----------------------------- 0.56s
ansible-nginx : enable HTTPs sites configs with existing certificates --- 0.52s
ansible-nginx : enable HTTP sites configs ------------------------------- 0.50s
ansible-nginx : validate variables -------------------------------------- 0.10s

# after

## first run

Donnerstag 15 Juni 2023  04:52:49 +0200 (0:00:00.670)       0:00:33.238 *******
===============================================================================
ansible-nginx : install nginx ------------------------------------------- 8.94s
ansible-nginx : create nginx sites directories -------------------------- 2.28s
ansible-nginx : create nginx main configuration ------------------------- 1.94s
ansible-nginx : copy vhost templates into temporary directory ----------- 1.70s
ansible-nginx : ensure vhosts root path exists -------------------------- 1.61s
ansible-nginx : create gzip configuration ------------------------------- 1.55s
ansible-nginx : propagate templates.tgz --------------------------------- 1.40s
ansible-nginx : create custom includes ---------------------------------- 1.30s
ansible-nginx : create logformat configuration -------------------------- 1.28s
ansible-nginx : extract instance/templates.tgz -------------------------- 1.14s
ansible-nginx : create HTTP vhost configurations ------------------------ 1.11s
ansible-nginx : reload service ------------------------------------------ 0.88s
ansible-nginx : ensure nginx is enabled on boot ------------------------- 0.67s
ansible-nginx : ensure vhosts log path exists --------------------------- 0.66s
ansible-nginx : create ssl configuration -------------------------------- 0.66s
ansible-nginx : create temporary directory on destination instance ------ 0.65s
ansible-nginx : find primary group for user 'www-data' ------------------ 0.65s
ansible-nginx : checking existing domains certificates ------------------ 0.64s
ansible-nginx : validate config ----------------------------------------- 0.63s
ansible-nginx : create HTTPs vhost configurations ----------------------- 0.63s

## second run

Donnerstag 15 Juni 2023  04:53:24 +0200 (0:00:00.897)       0:00:17.047 *******
===============================================================================
ansible-nginx : create nginx sites directories -------------------------- 2.19s
ansible-nginx : install nginx ------------------------------------------- 1.73s
ansible-nginx : ensure vhosts root path exists -------------------------- 1.64s
ansible-nginx : create HTTP vhost configurations ------------------------ 1.13s
ansible-nginx : create gzip configuration ------------------------------- 1.01s
ansible-nginx : create nginx main configuration ------------------------- 0.97s
ansible-nginx : create custom includes ---------------------------------- 0.90s
ansible-nginx : ensure nginx is enabled on boot ------------------------- 0.90s
ansible-nginx : create logformat configuration -------------------------- 0.85s
ansible-nginx : create ssl configuration -------------------------------- 0.65s
ansible-nginx : find primary group for user 'www-data' ------------------ 0.64s
ansible-nginx : create HTTPs vhost configurations ----------------------- 0.63s
ansible-nginx : checking existing domains certificates ------------------ 0.63s
ansible-nginx : ensure vhosts log path exists --------------------------- 0.63s
ansible-nginx : remove default site ------------------------------------- 0.55s
ansible-nginx : find templates archive on destination system ------------ 0.54s
ansible-nginx : find templates directory on destination system ---------- 0.52s
ansible-nginx : find templates archive on ansible controller ------------ 0.19s
ansible-nginx : validate variables -------------------------------------- 0.11s
ansible-nginx : copy vhost templates into temporary directory ----------- 0.07s


## third run

Donnerstag 15 Juni 2023  04:54:06 +0200 (0:00:00.861)       0:00:17.131 *******
===============================================================================
ansible-nginx : create nginx sites directories -------------------------- 2.24s
ansible-nginx : install nginx ------------------------------------------- 1.70s
ansible-nginx : ensure vhosts root path exists -------------------------- 1.65s
ansible-nginx : create HTTP vhost configurations ------------------------ 1.10s
ansible-nginx : create gzip configuration ------------------------------- 0.98s
ansible-nginx : create nginx main configuration ------------------------- 0.95s
ansible-nginx : create custom includes ---------------------------------- 0.89s
ansible-nginx : ensure nginx is enabled on boot ------------------------- 0.86s
ansible-nginx : create logformat configuration -------------------------- 0.86s
ansible-nginx : ensure vhosts log path exists --------------------------- 0.67s
ansible-nginx : find primary group for user 'www-data' ------------------ 0.66s
ansible-nginx : remove default site ------------------------------------- 0.66s
ansible-nginx : create HTTPs vhost configurations ----------------------- 0.64s
ansible-nginx : checking existing domains certificates ------------------ 0.62s
ansible-nginx : create ssl configuration -------------------------------- 0.62s
ansible-nginx : find templates archive on destination system ------------ 0.53s
ansible-nginx : find templates directory on destination system ---------- 0.53s
ansible-nginx : find templates archive on ansible controller ------------ 0.19s
ansible-nginx : validate variables -------------------------------------- 0.11s
ansible-nginx : copy vhost templates into temporary directory ----------- 0.06s


