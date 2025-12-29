from rest_framework import serializers
from django.utils import timezone
from datetime import datetime

class JobBatchAssignmentSerializer(serializers.Serializer):
    """
    Serializer pour l'affectation en lot de sessions et ressources aux jobs
    Supporte les comptages dynamiques (1, 2, 3, 4, 5, ...) via team1, team2, team3, team4, etc.
    """
    job_id = serializers.IntegerField(help_text="ID du job")
    resources = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="Liste des IDs de ressources à affecter au job (optionnel)"
    )

    def validate_job_id(self, value):
        """Valider job_id"""
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("job_id doit être un ID valide (nombre positif)")
        return value

    def validate_resources(self, value):
        """Valider la liste des ressources"""
        if value:
            for resource_id in value:
                if not isinstance(resource_id, int) or resource_id <= 0:
                    raise serializers.ValidationError(f"Ressource ID {resource_id} doit être un nombre positif")
        return value
    
    def to_internal_value(self, data):
        """
        Accepte les champs dynamiques team1, team2, team3, team4, etc.
        avec leurs counting_order et date correspondants
        """
        # Appeler la méthode parente pour valider les champs définis
        validated_data = super().to_internal_value(data)
        
        # Extraire tous les teams dynamiques (team1, team2, team3, etc.)
        teams_data = {}
        for key, value in data.items():
            if key.startswith('team') and key[4:].isdigit():
                team_num = int(key[4:])
                if value is not None:
                    if not isinstance(value, int) or value <= 0:
                        raise serializers.ValidationError(f"{key} doit être un ID valide (nombre positif)")
                    teams_data[team_num] = {
                        'session_id': value,
                        'counting_order': data.get(f'counting_order{team_num}', team_num),
                        'date': data.get(f'date{team_num}')
                    }
        
        validated_data['teams'] = teams_data
        return validated_data

class JobBatchAssignmentRequestSerializer(serializers.Serializer):
    """
    Serializer pour la requête d'affectation en lot (format direct)
    """
    def to_internal_value(self, data):
        """
        Accepte directement une liste de jobs ou une liste dans 'assignments'
        """
        try:
            if isinstance(data, list):
                # Format direct : [job1, job2, ...]
                return {'assignments': data}
            elif isinstance(data, dict) and 'assignments' in data:
                # Format avec clé assignments : {"assignments": [job1, job2, ...]}
                return data
            else:
                raise serializers.ValidationError("Format invalide. Attendu: liste de jobs ou {'assignments': [...]}")
        except Exception as e:
            raise serializers.ValidationError(f"Erreur de format: {str(e)}")

    assignments = serializers.ListField(
        child=JobBatchAssignmentSerializer(),
        min_length=1,
        help_text="Liste des jobs avec leurs affectations"
    )

    def validate_assignments(self, value):
        if not value:
            raise serializers.ValidationError("La liste des assignments ne peut pas être vide")
        
        try:
            job_ids = [job['job_id'] for job in value]
            if len(job_ids) != len(set(job_ids)):
                raise serializers.ValidationError("Les IDs des jobs doivent être uniques")
        except (KeyError, TypeError) as e:
            raise serializers.ValidationError(f"Format invalide dans assignments: {str(e)}")
        
        return value

    def validate(self, data):
        try:
            for job_data in data['assignments']:
                job_id = job_data.get('job_id')
                if not job_id:
                    raise serializers.ValidationError("job_id est obligatoire pour chaque job")
                
                teams = job_data.get('teams', {})
                has_resources = len(job_data.get('resources', [])) > 0
                
                # Vérifier qu'au moins une affectation est fournie
                if not (teams or has_resources):
                    raise serializers.ValidationError(
                        f"Le job {job_id} doit avoir au moins une affectation (team1, team2, team3, etc. ou resources)"
                    )
                
                # Vérifier les ordres de comptage et les doublons
                counting_orders = []
                for team_num, team_info in teams.items():
                    counting_order = team_info.get('counting_order', team_num)
                    if counting_order < 1:
                        raise serializers.ValidationError(
                            f"Le job {job_id} a un counting_order invalide pour team{team_num}: {counting_order}"
                        )
                    counting_orders.append(counting_order)
                    
                    # Si date n'est pas fournie, utiliser maintenant
                    if team_info.get('date') is None:
                        team_info['date'] = timezone.now()
                
                # Vérifier qu'il n'y a pas de doublons d'ordre de comptage
                if len(counting_orders) != len(set(counting_orders)):
                    duplicates = [order for order in counting_orders if counting_orders.count(order) > 1]
                    raise serializers.ValidationError(
                        f"Le job {job_id} a des ordres de comptage en double: {set(duplicates)}"
                    )
                        
        except Exception as e:
            raise serializers.ValidationError(f"Erreur de validation: {str(e)}")
        
        return data

class JobBatchAssignmentResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse d'affectation en lot
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    total_jobs_processed = serializers.IntegerField()
    jobs_results = serializers.ListField()
    processing_date = serializers.DateTimeField()

class JobReassignmentSerializer(serializers.Serializer):
    """
    Serializer pour la réaffectation d'une équipe à un job pour un comptage spécifique

    Format:
    {
        "job_id": 1,
        "team": 5,
        "counting_order": 1,
        "complete": true/false
    }
    """
    job_id = serializers.IntegerField(help_text="ID du job à réaffecter")
    team = serializers.IntegerField(help_text="ID de l'équipe (session) à affecter")
    counting_order = serializers.IntegerField(help_text="Ordre du comptage (1 ou 2)")
    complete = serializers.BooleanField(
        default=False,
        help_text="Si true, supprime toutes les données liées et remet à zéro"
    )

    def validate_job_id(self, value):
        """Valider job_id"""
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("job_id doit être un ID valide (nombre positif)")
        return value

    def validate_team(self, value):
        """Valider team (session ID)"""
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("team doit être un ID valide (nombre positif)")
        return value

    def validate_counting_order(self, value):
        """Valider counting_order"""
        if not isinstance(value, int) or value not in [1, 2]:
            raise serializers.ValidationError("counting_order doit être 1 ou 2")
        return value

class JobReassignmentRequestSerializer(serializers.Serializer):
    """
    Serializer pour la requête de réaffectation
    """
    job_id = serializers.IntegerField(help_text="ID du job à réaffecter")
    team = serializers.IntegerField(help_text="ID de l'équipe (session) à affecter")
    counting_order = serializers.IntegerField(help_text="Ordre du comptage (1 ou 2)")
    complete = serializers.BooleanField(
        default=False,
        help_text="Si true, supprime toutes les données liées et remet à zéro"
    )

    def validate_job_id(self, value):
        """Valider job_id"""
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("job_id doit être un ID valide (nombre positif)")
        return value

    def validate_team(self, value):
        """Valider team (session ID)"""
        if not isinstance(value, int) or value <= 0:
            raise serializers.ValidationError("team doit être un ID valide (nombre positif)")
        return value

    def validate_counting_order(self, value):
        """Valider counting_order"""
        if not isinstance(value, int) or value not in [1, 2]:
            raise serializers.ValidationError("counting_order doit être 1 ou 2")
        return value

class JobAssignmentResultSerializer(serializers.Serializer):
    """
    Serializer pour le résultat d'affectation d'un job
    """
    job_id = serializers.IntegerField()
    job_reference = serializers.CharField()
    assignments_created = serializers.IntegerField()
    assignments_updated = serializers.IntegerField()
    resources_created = serializers.IntegerField()
    resources_updated = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.CharField(),
        default=list
    ) 