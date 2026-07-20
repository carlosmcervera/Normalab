# Auth Testing Playbook — NormaLab

Admin: admin@normalab.com / Admin1234!

## API
```
curl -c cookies.txt -X POST $URL/api/auth/login -H "Content-Type: application/json" \
  -d '{"email":"admin@normalab.com","password":"Admin1234!"}'
curl -b cookies.txt $URL/api/auth/me
```
Login returns user object and sets access_token + refresh_token cookies.
/me returns the same user using those cookies.
