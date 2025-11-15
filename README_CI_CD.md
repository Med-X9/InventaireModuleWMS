# CI/CD - Guide de Référence Rapide

## 📦 Fichiers de Configuration

### Fichiers Principaux

- **`Jenkinsfile`** - Pipeline Jenkins principal
- **`jenkins-config.yml`** - Configuration des environnements et déploiements
- **`docker-compose.test.yml`** - Configuration Docker pour TEST
- **`docker-compose.prod.yml`** - Configuration Docker pour PRODUCTION
- **`.env.test.example`** - Template variables d'environnement TEST
- **`.env.prod.example`** - Template variables d'environnement PRODUCTION

## 🔄 Flux de Déploiement

```
┌─────────────┐
│ Git Push    │
│ dev/main    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Jenkins    │
│  Pipeline   │
└──────┬──────┘
       │
       ├──► SonarQube Analysis
       ├──► Build Docker Image
       ├──► Push to Docker Hub
       └──► Deploy to Server
              │
              ├──► TEST (dev branch) → 147.93.55.221
              └──► PROD (main branch) → 31.97.158.68
```

## 🎯 Branches et Environnements

| Branche | Environnement | Serveur | Image Tag | Compose File | Env File |
|---------|--------------|---------|-----------|--------------|----------|
| `dev` | TEST | 147.93.55.221 | `dev-latest` | `docker-compose.test.yml` | `.env.test` |
| `main` | PRODUCTION | 31.97.158.68 | `prod-latest` | `docker-compose.prod.yml` | `.env.prod` |

## 📋 Checklist de Déploiement

### Avant le Premier Déploiement

- [ ] Créer les fichiers `.env.test` et `.env.prod` sur les serveurs
- [ ] Configurer les credentials Jenkins
- [ ] Générer les clés secrètes Django (différentes pour chaque environnement)
- [ ] Configurer les bases de données
- [ ] Vérifier les accès SSH aux serveurs

### Déploiement TEST

1. Push sur branche `dev`
2. Jenkins exécute automatiquement le pipeline
3. Vérifier les logs : `docker-compose -f docker-compose.test.yml logs -f`

### Déploiement PRODUCTION

1. Merge `dev` → `main`
2. Push sur branche `main`
3. Jenkins exécute automatiquement le pipeline
4. Vérifier les logs : `docker-compose -f docker-compose.prod.yml logs -f`

## 🔧 Commandes Utiles

### Sur le Serveur TEST

```bash
# Voir les logs
docker-compose -f docker-compose.test.yml logs -f

# Redémarrer
docker-compose -f docker-compose.test.yml restart

# Arrêter
docker-compose -f docker-compose.test.yml down

# Exécuter une commande Django
docker-compose -f docker-compose.test.yml exec web python manage.py <command>
```

### Sur le Serveur PRODUCTION

```bash
# Voir les logs
docker-compose -f docker-compose.prod.yml logs -f

# Redémarrer
docker-compose -f docker-compose.prod.yml restart

# Arrêter
docker-compose -f docker-compose.prod.yml down

# Exécuter une commande Django
docker-compose -f docker-compose.prod.yml exec web python manage.py <command>
```

## 📚 Documentation Complète

- **[CI-CD_IMPLEMENTATION.md](./CI-CD_IMPLEMENTATION.md)** - Guide complet d'implémentation
- **[DEPLOYMENT_QUICK_START.md](./DEPLOYMENT_QUICK_START.md)** - Guide de déploiement rapide
- **[SECURITY.md](./SECURITY.md)** - Guide de sécurité

## 🆘 Support

En cas de problème, vérifier :
1. Les logs Jenkins
2. Les logs Docker sur le serveur
3. Les fichiers de configuration
4. La documentation complète

