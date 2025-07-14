# Documentation des APIs users (api/auth)

## POST /api/auth/login/
- **Description** : Authentification (JWT)
- **Méthode** : POST
- **Payload attendu** :
```json
{
  "username": "user1",
  "password": "motdepasse"
}
```
- **Réponse succès (200)** :
```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```
- **Réponse erreur (401)** :
```json
{
  "detail": "No active account found with the given credentials"
}
```
- **Statuts possibles** : 200, 401

---

## POST /api/auth/login/refresh/
- **Description** : Rafraîchir le token JWT
- **Méthode** : POST
- **Payload attendu** :
```json
{
  "refresh": "<refresh_token>"
}
```
- **Réponse succès (200)** :
```json
{
  "access": "<nouveau_access_token>"
}
```
- **Réponse erreur (401)** :
```json
{
  "detail": "Token is invalid or expired"
}
```
- **Statuts possibles** : 200, 401

---

## POST /api/auth/logout/
- **Description** : Déconnexion
- **Méthode** : POST
- **Réponse succès (200)** :
```json
{
  "detail": "Successfully logged out."
}
```
- **Statuts possibles** : 200

---

## GET /api/auth/mobile-users/
- **Description** : Liste des utilisateurs mobiles
- **Méthode** : GET
- **Réponse attendue (200)** :
```json
[
  {
    "id": 1,
    "username": "mobileuser1",
    "nom": "Dupont",
    "prenom": "Jean",
    "type": "Mobile"
  }
]
```
- **Statuts possibles** : 200

---

**Remarque :**
- Adapter les exemples selon la structure réelle des serializers et des vues.
- Pour plus de détails, consulter la documentation Swagger intégrée (`/swagger/`). 