# Guide de Sécurité - InventaireModuleWMS

Ce document décrit les mesures de sécurité implémentées dans le projet et les bonnes pratiques à suivre.

## 🔒 Mesures de Sécurité Implémentées

### 1. Configuration Django

#### SSL/TLS
- `SECURE_SSL_REDIRECT`: Redirection automatique vers HTTPS en production
- `SESSION_COOKIE_SECURE`: Cookies de session uniquement via HTTPS
- `CSRF_COOKIE_SECURE`: Cookies CSRF uniquement via HTTPS

#### HSTS (HTTP Strict Transport Security)
- `SECURE_HSTS_SECONDS`: 1 an en production
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`: Activé en production
- `SECURE_HSTS_PRELOAD`: Activé en production

#### Headers de Sécurité
- `X-Frame-Options: DENY`: Protection contre clickjacking
- `X-Content-Type-Options: nosniff`: Protection contre MIME sniffing
- `X-XSS-Protection: 1; mode=block`: Protection XSS
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`: Restriction des fonctionnalités du navigateur

### 2. Authentification et Autorisation

#### JWT (JSON Web Tokens)
- Durée d'accès: 1 jour (configurable)
- Durée de rafraîchissement: 7 jours
- Rotation automatique des tokens
- Blacklist des tokens révoqués

#### Rate Limiting
- **Login**: 5 tentatives par minute (protection force brute)
- **Refresh Token**: 10 rafraîchissements par minute
- **Verify Token**: 20 vérifications par minute
- **Utilisateurs anonymes**: 100 requêtes/heure
- **Utilisateurs authentifiés**: 1000 requêtes/heure

#### Permissions
- Toutes les vues protégées utilisent `IsAuthenticated`
- Permissions granulaires disponibles via Django permissions

### 3. Gestion des Erreurs

#### Exception Handler Personnalisé
- Ne pas exposer les stack traces en production
- Messages d'erreur génériques pour les clients
- Logs détaillés côté serveur uniquement
- Filtrage automatique des données sensibles dans les erreurs

### 4. Logging et Audit

#### Middleware de Logging
- Logs de toutes les actions utilisateur authentifiées
- Filtrage automatique des données sensibles (mots de passe, tokens)
- Rotation automatique des logs (5 MB, 5 backups)

#### Données Sensibles Filtrées
- `password`
- `token`
- `secret`
- `key`
- `api_key`
- `refresh`

### 5. CORS (Cross-Origin Resource Sharing)

- `CORS_ALLOW_ALL_ORIGINS=False` en production
- `CORS_ALLOWED_ORIGINS` configuré avec les domaines autorisés uniquement
- Headers CORS limités aux besoins

### 6. Base de Données

- Identifiants stockés dans variables d'environnement
- Connexion SSL/TLS recommandée en production
- Principe du moindre privilège pour l'utilisateur DB

## 📋 Checklist de Déploiement en Production

### Variables d'Environnement Requises

```bash
# Sécurité
IS_PRODUCTION=True
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<clé_secrète_unique_et_aléatoire>
DJANGO_ALLOWED_HOSTS=example.com,www.example.com

# SSL/TLS
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://example.com,https://www.example.com

# Base de données
POSTGRES_DB=<nom_db>
POSTGRES_USER=<user_db>
POSTGRES_PASSWORD=<mot_de_passe_fort>
POSTGRES_HOST=<host_db>
POSTGRES_PORT=5432

# Si derrière un reverse proxy (nginx)
# SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')
```

### Vérifications Pré-Déploiement

- [ ] `DEBUG=False` en production
- [ ] `SECRET_KEY` unique et aléatoire
- [ ] `ALLOWED_HOSTS` configuré correctement
- [ ] SSL/TLS activé et configuré
- [ ] Certificat SSL valide
- [ ] Headers de sécurité activés
- [ ] CORS configuré correctement
- [ ] Rate limiting activé
- [ ] Logs configurés et rotation activée
- [ ] Backups de base de données configurés
- [ ] Variables d'environnement sécurisées
- [ ] `.env` dans `.gitignore`
- [ ] Secrets non commités dans le code

## 🛡️ Bonnes Pratiques

### Développement

1. **Ne jamais commiter de secrets**
   - Utiliser `.env` pour les variables sensibles
   - Vérifier `.gitignore` contient `.env`

2. **Validation des entrées**
   - Toujours valider les données dans les serializers
   - Utiliser les validators Django/DRF

3. **Requêtes ORM sécurisées**
   - Utiliser l'ORM Django (protection SQL injection)
   - Éviter les requêtes SQL brutes
   - Filtrer les requêtes par permissions utilisateur

4. **Gestion des erreurs**
   - Ne pas exposer de stack traces
   - Logger les erreurs détaillées côté serveur
   - Messages d'erreur génériques pour les clients

### Production

1. **Monitoring**
   - Surveiller les tentatives de login échouées
   - Alertes sur activités suspectes
   - Monitoring des performances

2. **Mises à jour**
   - Mettre à jour les dépendances régulièrement
   - Scanner les vulnérabilités (`pip-audit`, `safety`)
   - Tester les mises à jour en staging

3. **Backups**
   - Backups réguliers de la base de données
   - Test de restauration périodique
   - Stockage sécurisé des backups

## 🔍 Audit de Sécurité

### Outils Recommandés

- `pip-audit`: Scan des vulnérabilités Python
- `safety`: Scan des dépendances
- `bandit`: Analyse statique de code Python
- `django-security-check`: Vérification des settings Django

### Commandes

```bash
# Scan des vulnérabilités
pip install pip-audit
pip-audit

# Scan des dépendances
pip install safety
safety check

# Analyse statique
pip install bandit
bandit -r apps/ project/
```

## 📞 Contact Sécurité

En cas de découverte d'une vulnérabilité de sécurité, merci de contacter l'équipe de sécurité.

## 📚 Ressources

- [Django Security Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django REST Framework Security](https://www.django-rest-framework.org/topics/security/)

