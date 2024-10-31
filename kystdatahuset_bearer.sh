curl -X 'POST' \
  'https://kystdatahuset.no/ws/api/auth/login' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "'"$KYSTDATAHUSET_USERNAME"'",
  "password": "'"$KYSTDATAHUSET_PASSWORD"'"
}'
