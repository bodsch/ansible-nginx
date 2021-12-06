#!/usr/bin/env bash

set -e

. /usr/local/etc/certbot_renew.rc

exit_hook() {
  # clean up
  rm -vf "${WELL_KNOWN_DIRECTORY}/*"
}
trap exit_hook INT TERM QUIT EXIT

check_certificates() {

  echo "current certificates"
  certbot certificates
}

file_age() {
  FILE_CREATED_TIME=$(date -r "${1}" +%s)
  TIME_NOW=$(date +%s)
  echo "$[ ${TIME_NOW} - ${FILE_CREATED_TIME} ]"
}

test_well_known() {

  echo "test .well-known challenge"

  count_err=0

  for d in ${1}
  do
    echo "  - ${d}"
    uuid=$(tr -cd '[:alnum:]' < /dev/urandom | fold -w42 | head -n1)
    touch "${WELL_KNOWN_DIRECTORY}/${uuid}"
    set +e
    state=$(curl \
      --silent \
      --head \
      --output /dev/null \
      --write-out "%{http_code}" \
      http://${d}/.well-known/acme-challenge/${uuid})

    rm --force "${WELL_KNOWN_DIRECTORY}/${uuid}"

    if [ "${state}" == 200 ]
    then
      echo "[NOTE] ${d} working"
    else
      count_err=$(expr ${count_err} + 1)
      echo "[ERROR] ${d} has no valid .well-know directory handling."
    fi
  done

  if [ ${count_err} -gt 0 ]
  then
    exit 1
  fi

  echo "all domains working"
  set -e
}

define_domains() {

  ca_domains=$(openssl x509 \
    -in "/etc/letsencrypt/live/$1/fullchain.pem" \
    -text \
    -noout | \
    grep 'DNS:' | \
      sed -r -e 's/DNS://g' | \
      sed -r -e 's/,//g' | \
      sed 's/^[[:space:]]*//g')

  echo "${ca_domains}"
}

run() {

  pushd "${lets_encrypt_ca}" > /dev/null

#  check_certificates

  # Go through all domains and check if certificates need to renew
  for domain in $(ls -1 "${lets_encrypt_ca}")
  do
    [ -d "${lets_encrypt_ca}/${domain}" ] || continue

    cert_file="${lets_encrypt_ca}/${domain}/fullchain.pem"
    key_file="${lets_encrypt_ca}/${domain}/privkey.pem"

    if [ -f ${cert_file} ] && [ -f ${key_file} ]
    then
      # check expire date
      enddate=$(openssl x509 -enddate -noout -in ${cert_file} | cut -d'=' -f2)
      exp=$(date -d "${enddate}" +%s)

      # what is now?
      datenow=$(date -d "now" +%s)

      # how many days until CA expires?
      days_exp=$(echo \( ${exp} - ${datenow} \) / 86400 | bc)

      echo "Checking expiration date for ${domain} ..."

      if [ "${days_exp}" -gt "${exp_limit}" ]
      then
        echo "[NOTE] nothing to do, cert is up to day. renewal in ${days_exp} days."
      else
        echo "[NOTE] will try to renew cert for ${domain}. renewal in ${days_exp} days."

        DOMAINS=$(define_domains "${domain}")
        DOMAINS=$(echo "${DOMAINS}" | xargs -n1 | sort | xargs)
        DOMAINS_OVERWRITE=$(echo "${DOMAINS_OVERWRITE}" | xargs -n1 | sort | xargs)

        CHECKSUM_DOMAINS=$(echo "{DOMAINS}" | sha256sum | cut -d' ' -f1)
        CHECKSUM_DOMAINS_OVERWRITE=$(echo "{DOMAINS_OVERWRITE}" | sha256sum | cut -d' ' -f1)

        if [ "${CHECKSUM_DOMAINS}" != "${CHECKSUM_DOMAINS_OVERWRITE}" ]
        then
          DOMAINS="${DOMAINS_OVERWRITE}"
        fi

        echo "${DOMAINS}"
        echo "${DOMAINS_OVERWRITE}"
        test_well_known "${DOMAINS_OVERWRITE}"

        certbot_domains=""
        # create domain var for certbot
        for d in ${DOMAINS_OVERWRITE}
        do
          certbot_domains="${certbot_domains} --domain ${d}"
        done

        echo "${certbot_domains}"

        CERTBOT_RENEW_OPTS="renew --dry-run --webroot --webroot-path /srv/www/letsencrypt ${certbot_domains}  " # --agree-tos ${CERTBOT_EMAIL}"
        CERTBOT_CERTONLY_OPTS="certonly --expand --webroot --webroot-path /srv/www/letsencrypt --cert-name "home.boone-schulz.de"  ${certbot_domains} --verbose " # --agree-tos ${CERTBOT_EMAIL}"

        certbot ${CERTBOT_RENEW_OPTS}

        nginx -s reload
      fi
    fi

    echo ""
  done

  popd > /dev/null
}

