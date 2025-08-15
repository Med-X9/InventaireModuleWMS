# API des Assignments et Jobs

## Vue d'ensemble

Cette API permet de mettre à jour automatiquement le statut d'un assignment et de son job vers "ENTAME". Elle inclut des vérifications de sécurité pour s'assurer que seuls les utilisateurs affectés à un assignment peuvent modifier ses statuts.

## Endpoint unique

### Mise à jour des statuts d'un assignment et de son job

**URL:** `POST /mobile/api/user/{user_id}/assignment/{assignment_id}/status/`

**Description:** Met à jour automatiquement le statut d'un assignment et de son job vers "ENTAME"

**Headers requis:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Body:** Aucun body requis - le statut "ENTAME" est appliqué automatiquement

**Statut appliqué:** `ENTAME` (automatique)

**Réponse de succès (200):**
```json
{
    "success": true,
    "data": {
        "assignment": {
            "id": 1,
            "reference": "ASS-123-4567-ABCD",
            "status": "ENTAME",
            "updated_at": "2024-01-15T10:30:00Z"
        },
        "job": {
            "id": 1,
            "reference": "JOB-123-4567-ABCD",
            "status": "ENTAME",
            "updated_at": "2024-01-15T10:30:00Z"
        },
        "message": "Assignment et job mis à jour vers le statut ENTAME"
    }
}
```

## Sécurité

- **Authentification:** Token Bearer requis
- **Autorisation:** L'utilisateur doit être affecté à l'assignment
- **Validation:** Seules les transitions de statut autorisées sont acceptées

## Utilisation avec cURL

### Mise à jour des statuts (sans body)
```bash
curl -X POST \
  http://localhost:8000/mobile/api/user/1/assignment/1/status/ \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json'
```

## Codes d'erreur

- **400:** Transition de statut non autorisée
- **401:** Authentification requise
- **403:** Utilisateur non autorisé pour cet assignment
- **404:** Assignment ou job non trouvé
- **500:** Erreur interne du serveur

## Test

Pour tester l'API, exécutez :
```bash
python test_api_simple.py
```

**Note:** Remplacez les IDs d'utilisateur et d'assignment par des valeurs valides dans votre base de données.

## Fonctionnalités

- ✅ Mise à jour automatique vers le statut "ENTAME"
- ✅ Aucun body requis dans la requête
- ✅ Vérification que l'utilisateur est affecté à l'assignment
- ✅ Validation des transitions de statut autorisées
- ✅ Mise à jour automatique des dates correspondantes
- ✅ Transaction atomique pour garantir la cohérence des données
