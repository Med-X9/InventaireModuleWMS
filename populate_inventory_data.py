"""
Script pour remplir les tables de l'app inventory avec des données complètes
Basé sur les données de masterdata avec tous les cas possibles
"""

import os
import django
from datetime import datetime, timedelta
from django.utils import timezone
import uuid
import hashlib

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import (
    Inventory, Setting, Planning, Counting, Job, Personne,
    JobDetail, Assigment, JobDetailRessource, InventoryDetailRessource,
    CountingDetail, NSerieInventory, EcartComptage
)
from apps.masterdata.models import (
    Account, Warehouse, Location, Product, NSerie, Ressource, 
    TypeRessource, UnitOfMeasure, Stock
)
from apps.users.models import UserApp
from django.contrib.auth.hashers import make_password


def generate_unique_reference(prefix, index=0):
    """Génère une référence unique pour les modèles"""
    temp_id = str(uuid.uuid4())[:6]
    timestamp = int(timezone.now().timestamp())
    timestamp_short = str(timestamp)[-4:]
    data_to_hash = f"{prefix}{temp_id}{timestamp}{index}"
    hash_value = hashlib.md5(data_to_hash.encode()).hexdigest()[:4].upper()
    reference = f"{prefix}-{temp_id}-{timestamp_short}-{hash_value}"[:20]
    return reference


def clear_inventory_data():
    """Nettoyer toutes les données de l'app inventory"""
    print("\n🗑️  Suppression des anciennes données...")
    
    # Ordre important pour respecter les contraintes de clés étrangères
    EcartComptage.objects.all().delete()
    NSerieInventory.objects.all().delete()
    CountingDetail.objects.all().delete()
    InventoryDetailRessource.objects.all().delete()
    JobDetailRessource.objects.all().delete()
    Assigment.objects.all().delete()
    JobDetail.objects.all().delete()
    Job.objects.all().delete()
    Personne.objects.all().delete()
    Counting.objects.all().delete()
    Planning.objects.all().delete()
    Setting.objects.all().delete()
    Inventory.objects.all().delete()
    
    print("✅ Anciennes données supprimées")


def create_test_users():
    """Créer des utilisateurs de test pour les affectations"""
    print("\n👥 Création des utilisateurs de test...")
    
    # Récupérer un compte existant pour associer les utilisateurs
    accounts = list(Account.objects.filter(account_statuts='ACTIVE')[:3])
    if not accounts:
        print("   ⚠️  Aucun compte actif trouvé. Création d'un compte de test...")
        account = Account.objects.create(
            account_name='Compte Test Mobile',
            account_statuts='ACTIVE',
            description='Compte de test pour utilisateurs mobiles'
        )
        accounts = [account]
    else:
        print(f"   → {len(accounts)} compte(s) actif(s) trouvé(s)")
    
    users = []
    user_data = [
        {'username': 'mobile_user1', 'type': 'Mobile', 'nom': 'Durand', 'prenom': 'Marc'},
        {'username': 'mobile_user2', 'type': 'Mobile', 'nom': 'Lefebvre', 'prenom': 'Julie'},
        {'username': 'mobile_user3', 'type': 'Mobile', 'nom': 'Moreau', 'prenom': 'Thomas'},
    ]
    
    for i, data in enumerate(user_data):
        user, created = UserApp.objects.get_or_create(
            username=data['username'],
            defaults={
                'type': data['type'],
                'nom': data['nom'],
                'prenom': data['prenom'],
                'compte': accounts[i % len(accounts)],  # Associer un compte
                'password': make_password('password123')
            }
        )
        # Si l'utilisateur existe déjà mais n'a pas de compte, l'ajouter
        if not created and not user.compte:
            user.compte = accounts[i % len(accounts)]
            user.nom = data['nom']
            user.prenom = data['prenom']
            user.save()
            print(f"   ✓ Utilisateur mis à jour avec compte: {user.username} ({user.prenom} {user.nom})")
        elif created:
            print(f"   ✓ Utilisateur créé: {user.username} ({user.prenom} {user.nom}) - Compte: {user.compte.account_name}")
        else:
            print(f"   → Utilisateur existant: {user.username} ({user.prenom} {user.nom}) - Compte: {user.compte.account_name if user.compte else 'Aucun'}")
        
        users.append(user)
    
    return users


def create_personnes():
    """Créer des personnes pour les affectations"""
    print("\n👤 Création des personnes...")
    
    personnes_data = [
        {'nom': 'Dupont', 'prenom': 'Jean'},
        {'nom': 'Martin', 'prenom': 'Marie'},
        {'nom': 'Bernard', 'prenom': 'Pierre'},
        {'nom': 'Dubois', 'prenom': 'Sophie'},
        {'nom': 'Thomas', 'prenom': 'Luc'},
        {'nom': 'Robert', 'prenom': 'Claire'},
    ]
    
    personnes = []
    for i, data in enumerate(personnes_data):
        # Créer d'abord l'objet sans le sauvegarder
        personne = Personne(**data)
        # Générer manuellement une référence unique
        personne.reference = generate_unique_reference('PER', i)
        personne.save()
        personnes.append(personne)
        print(f"   ✓ Personne créée: {personne.nom} {personne.prenom} ({personne.reference})")
    
    return personnes


def create_inventories():
    """Créer des inventaires avec tous les statuts et types possibles"""
    print("\n📦 Création des inventaires...")
    
    now = timezone.now()
    
    inventories_data = [
        {
            'label': 'Inventaire Général 2025 Q1',
            'date': now,
            'status': 'EN PREPARATION',
            'inventory_type': 'GENERAL',
            'en_preparation_status_date': now,
        },
        {
            'label': 'Inventaire Tournant Zone A - Janvier',
            'date': now + timedelta(days=1),
            'status': 'EN REALISATION',
            'inventory_type': 'TOURNANT',
            'en_preparation_status_date': now - timedelta(days=5),
            'en_realisation_status_date': now - timedelta(days=2),
        },
        {
            'label': 'Inventaire Général 2024 Q4',
            'date': now - timedelta(days=30),
            'status': 'TERMINE',
            'inventory_type': 'GENERAL',
            'en_preparation_status_date': now - timedelta(days=40),
            'en_realisation_status_date': now - timedelta(days=35),
            'termine_status_date': now - timedelta(days=30),
        },
        {
            'label': 'Inventaire Tournant Zone B - Décembre',
            'date': now - timedelta(days=60),
            'status': 'CLOTURE',
            'inventory_type': 'TOURNANT',
            'en_preparation_status_date': now - timedelta(days=70),
            'en_realisation_status_date': now - timedelta(days=65),
            'termine_status_date': now - timedelta(days=62),
            'cloture_status_date': now - timedelta(days=60),
        },
        {
            'label': 'Inventaire Général Annuel 2025',
            'date': now + timedelta(days=7),
            'status': 'EN PREPARATION',
            'inventory_type': 'GENERAL',
            'en_preparation_status_date': now,
        },
    ]
    
    inventories = []
    for i, data in enumerate(inventories_data):
        inventory = Inventory(**data)
        inventory.reference = generate_unique_reference('INV', i)
        inventory.save()
        inventories.append(inventory)
        print(f"   ✓ Inventaire créé: {inventory.label} [{inventory.status}] ({inventory.reference})")
    
    return inventories


def create_settings(inventories):
    """Créer les paramètres (Settings) pour les inventaires"""
    print("\n⚙️  Création des paramètres (Settings)...")
    
    # Récupérer les comptes et entrepôts existants
    accounts = list(Account.objects.filter(account_statuts='ACTIVE')[:3])
    warehouses = list(Warehouse.objects.filter(status='ACTIVE')[:3])
    
    if not accounts:
        print("   ⚠️  Aucun compte actif trouvé. Création d'un compte de test...")
        account = Account.objects.create(
            account_name='Compte Test',
            account_statuts='ACTIVE',
            description='Compte de test pour inventaire'
        )
        accounts = [account]
    
    if not warehouses:
        print("   ⚠️  Aucun entrepôt actif trouvé. Création d'un entrepôt de test...")
        warehouse = Warehouse.objects.create(
            warehouse_name='Entrepôt Central Test',
            warehouse_type='CENTRAL',
            status='ACTIVE',
            description='Entrepôt de test pour inventaire'
        )
        warehouses = [warehouse]
    
    settings = []
    setting_index = 0
    for inventory in inventories[:3]:  # Limiter aux 3 premiers inventaires
        for i, account in enumerate(accounts):
            setting = Setting(
                account=account,
                warehouse=warehouses[i % len(warehouses)],
                inventory=inventory
            )
            setting.reference = generate_unique_reference('SET', setting_index)
            setting.save()
            settings.append(setting)
            setting_index += 1
            print(f"   ✓ Setting créé: {setting.account.account_name} - {setting.warehouse.warehouse_name} ({setting.reference})")
    
    return settings


def create_plannings(inventories):
    """Créer des plannings pour les inventaires"""
    print("\n📅 Création des plannings...")
    
    warehouses = list(Warehouse.objects.filter(status='ACTIVE')[:3])
    if not warehouses:
        print("   ⚠️  Aucun entrepôt disponible")
        return []
    
    plannings = []
    now = timezone.now()
    
    for i, inventory in enumerate(inventories[:3]):
        planning = Planning(
            start_date=now + timedelta(days=i*7),
            end_date=now + timedelta(days=i*7 + 5),
            inventory=inventory,
            warehouse=warehouses[i % len(warehouses)]
        )
        planning.reference = generate_unique_reference('PLN', i)
        planning.save()
        plannings.append(planning)
        print(f"   ✓ Planning créé: {planning.warehouse.warehouse_name} - {planning.inventory.label} ({planning.reference})")
    
    return plannings


def create_countings(inventories):
    """Créer des comptages avec tous les cas de configuration possibles"""
    print("\n🔢 Création des comptages (tous les cas)...")
    
    # Configurations de comptage représentant tous les cas possibles
    # Modes valides: "en vrac", "par article", "image de stock"
    counting_configs = [
        # Cas 1: Image de stock - 1er comptage
        {
            'order': 1,
            'count_mode': 'image de stock',
            'unit_scanned': False,
            'entry_quantity': True,
            'is_variant': False,
            'n_lot': False,
            'n_serie': False,
            'dlc': False,
            'show_product': True,
            'stock_situation': True,
            'quantity_show': True,
        },
        # Cas 2: En vrac - 2ème comptage (simple)
        {
            'order': 2,
            'count_mode': 'en vrac',
            'unit_scanned': False,
            'entry_quantity': True,
            'is_variant': False,
            'n_lot': False,
            'n_serie': False,
            'dlc': False,
            'show_product': False,
            'stock_situation': False,
            'quantity_show': False,
        },
        # Cas 3: Par article - 3ème comptage avec lots
        {
            'order': 3,
            'count_mode': 'par article',
            'unit_scanned': False,
            'entry_quantity': True,
            'is_variant': False,
            'n_lot': True,
            'n_serie': False,
            'dlc': False,
            'show_product': True,
            'stock_situation': False,
            'quantity_show': True,
        },
        # Cas 4: Par article avec numéros de série
        {
            'order': 1,
            'count_mode': 'par article',
            'unit_scanned': True,
            'entry_quantity': False,
            'is_variant': False,
            'n_lot': False,
            'n_serie': True,
            'dlc': False,
            'show_product': True,
            'stock_situation': True,
            'quantity_show': False,
        },
        # Cas 5: Par article avec DLC
        {
            'order': 2,
            'count_mode': 'par article',
            'unit_scanned': False,
            'entry_quantity': True,
            'is_variant': False,
            'n_lot': False,
            'n_serie': False,
            'dlc': True,
            'show_product': True,
            'stock_situation': False,
            'quantity_show': True,
        },
        # Cas 6: Par article avec variantes
        {
            'order': 3,
            'count_mode': 'par article',
            'unit_scanned': False,
            'entry_quantity': True,
            'is_variant': True,
            'n_lot': False,
            'n_serie': False,
            'dlc': False,
            'show_product': True,
            'stock_situation': True,
            'quantity_show': True,
        },
        # Cas 7: Par article avec lot + DLC
        {
            'order': 1,
            'count_mode': 'par article',
            'unit_scanned': False,
            'entry_quantity': True,
            'is_variant': False,
            'n_lot': True,
            'n_serie': False,
            'dlc': True,
            'show_product': True,
            'stock_situation': True,
            'quantity_show': True,
        },
        # Cas 8: Par article avec série et scan d'unité
        {
            'order': 2,
            'count_mode': 'par article',
            'unit_scanned': True,
            'entry_quantity': False,
            'is_variant': False,
            'n_lot': False,
            'n_serie': True,
            'dlc': False,
            'show_product': False,
            'stock_situation': True,
            'quantity_show': False,
        },
        # Cas 9: En vrac - comptage aveugle (sans affichage)
        {
            'order': 3,
            'count_mode': 'en vrac',
            'unit_scanned': False,
            'entry_quantity': True,
            'is_variant': False,
            'n_lot': False,
            'n_serie': False,
            'dlc': False,
            'show_product': False,
            'stock_situation': False,
            'quantity_show': False,
        },
        # Cas 10: Par article - comptage complet (toutes options)
        {
            'order': 1,
            'count_mode': 'par article',
            'unit_scanned': True,
            'entry_quantity': True,
            'is_variant': True,
            'n_lot': True,
            'n_serie': True,
            'dlc': True,
            'show_product': True,
            'stock_situation': True,
            'quantity_show': True,
        },
    ]
    
    countings = []
    counting_index = 0
    for inventory in inventories[:2]:  # Utiliser les 2 premiers inventaires
        for config in counting_configs:
            counting = Counting(
                inventory=inventory,
                **config
            )
            counting.reference = generate_unique_reference('CNT', counting_index)
            counting.save()
            countings.append(counting)
            counting_index += 1
            options = []
            if config['n_lot']: options.append('LOT')
            if config['n_serie']: options.append('SÉRIE')
            if config['dlc']: options.append('DLC')
            if config['is_variant']: options.append('VARIANTE')
            options_str = ', '.join(options) if options else 'Aucune'
            print(f"   ✓ Comptage créé: {config['count_mode']} - Options: {options_str} ({counting.reference})")
    
    return countings


def create_jobs(inventories):
    """Créer des jobs avec tous les statuts possibles"""
    print("\n💼 Création des jobs (tous les statuts)...")
    
    warehouses = list(Warehouse.objects.filter(status='ACTIVE')[:3])
    if not warehouses:
        print("   ⚠️  Aucun entrepôt disponible")
        return []
    
    now = timezone.now()
    
    # Tous les statuts possibles avec leurs dates
    job_statuses = [
        {
            'status': 'EN ATTENTE',
            'en_attente_date': now,
        },
        {
            'status': 'AFFECTE',
            'en_attente_date': now - timedelta(days=3),
            'affecte_date': now - timedelta(days=2),
        },
        {
            'status': 'PRET',
            'en_attente_date': now - timedelta(days=5),
            'affecte_date': now - timedelta(days=4),
            'pret_date': now - timedelta(days=3),
        },
        {
            'status': 'TRANSFERT',
            'en_attente_date': now - timedelta(days=6),
            'affecte_date': now - timedelta(days=5),
            'pret_date': now - timedelta(days=4),
            'transfert_date': now - timedelta(days=3),
        },
        {
            'status': 'ENTAME',
            'en_attente_date': now - timedelta(days=7),
            'affecte_date': now - timedelta(days=6),
            'pret_date': now - timedelta(days=5),
            'transfert_date': now - timedelta(days=4),
            'entame_date': now - timedelta(days=2),
        },
        {
            'status': 'VALIDE',
            'en_attente_date': now - timedelta(days=10),
            'affecte_date': now - timedelta(days=9),
            'pret_date': now - timedelta(days=8),
            'transfert_date': now - timedelta(days=7),
            'entame_date': now - timedelta(days=5),
            'valide_date': now - timedelta(days=2),
        },
        {
            'status': 'TERMINE',
            'en_attente_date': now - timedelta(days=15),
            'affecte_date': now - timedelta(days=14),
            'pret_date': now - timedelta(days=13),
            'transfert_date': now - timedelta(days=12),
            'entame_date': now - timedelta(days=10),
            'valide_date': now - timedelta(days=5),
            'termine_date': now - timedelta(days=2),
        },
        {
            'status': 'SAISIE MANUELLE',
            'en_attente_date': now - timedelta(days=8),
            'saisie_manuelle_date': now - timedelta(days=1),
        },
    ]
    
    jobs = []
    for i, status_data in enumerate(job_statuses):
        job = Job(
            warehouse=warehouses[i % len(warehouses)],
            inventory=inventories[i % len(inventories)],
            **status_data
        )
        job.reference = generate_unique_reference('JOB', i)
        job.save()
        jobs.append(job)
        print(f"   ✓ Job créé: {status_data['status']} - {job.warehouse.warehouse_name} ({job.reference})")
    
    return jobs


def create_job_details(jobs, countings):
    """Créer des détails de jobs par emplacement"""
    print("\n📋 Création des détails de jobs (JobDetail)...")
    
    locations = list(Location.objects.filter(is_active=True)[:20])
    if not locations:
        print("   ⚠️  Aucun emplacement actif trouvé")
        return []
    
    job_details = []
    now = timezone.now()
    detail_index = 0
    
    for i, job in enumerate(jobs[:5]):  # Limiter aux 5 premiers jobs
        # Créer plusieurs JobDetail pour chaque job
        for j in range(min(3, len(locations))):
            location = locations[(i * 3 + j) % len(locations)]
            counting = countings[i % len(countings)] if countings else None
            
            status = 'TERMINE' if i % 2 == 0 else 'EN ATTENTE'
            job_detail = JobDetail(
                location=location,
                job=job,
                counting=counting,
                status=status,
                en_attente_date=now - timedelta(days=2) if status == 'EN ATTENTE' else now - timedelta(days=5),
                termine_date=now - timedelta(days=1) if status == 'TERMINE' else None
            )
            job_detail.reference = generate_unique_reference('JBD', detail_index)
            job_detail.save()
            job_details.append(job_detail)
            detail_index += 1
            print(f"   ✓ JobDetail créé: {job.reference} - {location.location_reference} [{status}] ({job_detail.reference})")
    
    return job_details


def create_assignments(jobs, personnes, countings, users):
    """Créer des affectations avec toutes les combinaisons"""
    print("\n👥 Création des affectations (Assigment)...")
    
    assignments = []
    now = timezone.now()
    
    statuses = ['EN ATTENTE', 'AFFECTE', 'PRET', 'TRANSFERT', 'ENTAME', 'TERMINE']
    
    for i, job in enumerate(jobs[:6]):  # Limiter aux 6 premiers jobs
        status = statuses[i % len(statuses)]
        
        # Certaines affectations ont 1 personne, d'autres 2
        personne_one = personnes[i % len(personnes)]
        personne_two = personnes[(i + 1) % len(personnes)] if i % 2 == 0 else None
        
        counting = countings[i % len(countings)] if countings else None
        session = users[i % len(users)] if i % 3 == 0 else None
        
        assignment_data = {
            'job': job,
            'counting': counting,
            'status': status,
            'personne': personne_one,
            'personne_two': personne_two,
            'session': session,
            'date_start': now - timedelta(days=i+1),
        }
        
        # Ajouter les dates selon le statut
        if status in ['AFFECTE', 'PRET', 'TRANSFERT', 'ENTAME', 'TERMINE']:
            assignment_data['affecte_date'] = now - timedelta(days=i+1)
        if status in ['PRET', 'TRANSFERT', 'ENTAME', 'TERMINE']:
            assignment_data['pret_date'] = now - timedelta(days=i)
        if status in ['TRANSFERT', 'ENTAME', 'TERMINE']:
            assignment_data['transfert_date'] = now - timedelta(days=i-1)
        if status in ['ENTAME', 'TERMINE']:
            assignment_data['entame_date'] = now - timedelta(days=max(1, i-2))
        
        assignment = Assigment(**assignment_data)
        assignment.reference = generate_unique_reference('ASS', i)
        assignment.save()
        assignments.append(assignment)
        
        personnes_str = f"{personne_one.nom}"
        if personne_two:
            personnes_str += f" + {personne_two.nom}"
        
        print(f"   ✓ Affectation créée: {job.reference} - {personnes_str} [{status}] ({assignment.reference})")
    
    return assignments


def create_ressources_if_needed():
    """Créer des ressources de test si elles n'existent pas"""
    print("\n🔧 Vérification des ressources...")
    
    # Chercher ou créer un type de ressource
    type_ressource = TypeRessource.objects.filter(libelle='Terminal Mobile').first()
    if not type_ressource:
        try:
            type_ressource = TypeRessource.objects.create(
                libelle='Terminal Mobile',
                description='Terminal de saisie mobile'
            )
            print(f"   ✓ Type de ressource créé: {type_ressource.libelle}")
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la création du type de ressource: {e}")
            # Essayer de récupérer un type existant
            type_ressource = TypeRessource.objects.first()
            if not type_ressource:
                raise Exception("Impossible de créer ou récupérer un type de ressource")
    else:
        print(f"   → Type de ressource existant: {type_ressource.libelle}")
    
    # Créer des ressources si nécessaire
    ressources = []
    ressources_data = [
        {'libelle': 'Terminal 001', 'status': 'ACTIVE'},
        {'libelle': 'Terminal 002', 'status': 'ACTIVE'},
        {'libelle': 'Scanner Zebra 01', 'status': 'ACTIVE'},
        {'libelle': 'Scanner Zebra 02', 'status': 'INACTIVE'},
    ]
    
    for data in ressources_data:
        ressource = Ressource.objects.filter(libelle=data['libelle']).first()
        if not ressource:
            try:
                ressource = Ressource.objects.create(
                    libelle=data['libelle'],
                    type_ressource=type_ressource,
                    status=data['status'],
                    description=f"Ressource de test - {data['libelle']}"
                )
                print(f"   ✓ Ressource créée: {ressource.libelle}")
            except Exception as e:
                print(f"   ⚠️  Erreur lors de la création de {data['libelle']}: {e}")
                continue
        else:
            print(f"   → Ressource existante: {ressource.libelle}")
        ressources.append(ressource)
    
    if not ressources:
        # Si aucune ressource n'a été créée, prendre les ressources existantes
        ressources = list(Ressource.objects.all()[:4])
    
    return ressources


def create_job_detail_ressources(jobs, ressources):
    """Créer des liens entre jobs et ressources"""
    print("\n🔗 Création des ressources de jobs (JobDetailRessource)...")
    
    job_detail_ressources = []
    
    for i, job in enumerate(jobs[:4]):
        ressource = ressources[i % len(ressources)]
        quantity = (i % 3) + 1
        
        jdr = JobDetailRessource(
            job=job,
            ressource=ressource,
            quantity=quantity
        )
        jdr.reference = generate_unique_reference('JDR', i)
        jdr.save()
        job_detail_ressources.append(jdr)
        print(f"   ✓ JobDetailRessource créé: {job.reference} - {ressource.libelle} x{quantity} ({jdr.reference})")
    
    return job_detail_ressources


def create_inventory_detail_ressources(inventories, ressources):
    """Créer des liens entre inventaires et ressources"""
    print("\n🔗 Création des ressources d'inventaire (InventoryDetailRessource)...")
    
    inventory_detail_ressources = []
    idr_index = 0
    
    for i, inventory in enumerate(inventories[:3]):
        for j in range(2):  # 2 ressources par inventaire
            ressource = ressources[(i + j) % len(ressources)]
            quantity = ((i + j) % 5) + 1
            
            idr = InventoryDetailRessource(
                inventory=inventory,
                ressource=ressource,
                quantity=quantity
            )
            idr.reference = generate_unique_reference('IDR', idr_index)
            idr.save()
            inventory_detail_ressources.append(idr)
            idr_index += 1
            print(f"   ✓ InventoryDetailRessource créé: {inventory.reference} - {ressource.libelle} x{quantity} ({idr.reference})")
    
    return inventory_detail_ressources


def create_counting_details(countings):
    """Créer des détails de comptage avec tous les cas"""
    print("\n📊 Création des détails de comptage (CountingDetail)...")
    
    locations = list(Location.objects.filter(is_active=True)[:10])
    products = list(Product.objects.filter(Product_Status='ACTIVE')[:15])
    
    if not locations:
        print("   ⚠️  Aucun emplacement actif trouvé")
        return []
    
    if not products:
        print("   ⚠️  Aucun produit actif trouvé")
        return []
    
    counting_details = []
    now = timezone.now()
    cd_index = 0
    
    for i, counting in enumerate(countings[:10]):  # Limiter aux 10 premiers comptages
        # Créer plusieurs détails de comptage pour chaque comptage
        for j in range(min(5, len(products))):
            location = locations[(i + j) % len(locations)]
            product = products[j % len(products)]
            quantity = (i * 10 + j * 5) % 100 + 1
            
            # Configuration selon le comptage
            detail_data = {
                'counting': counting,
                'location': location,
                'product': product,
                'quantity_inventoried': quantity,
                'last_synced_at': now - timedelta(hours=i)
            }
            
            # Ajouter n_lot si le comptage le requiert
            if counting.n_lot and product.n_lot:
                detail_data['n_lot'] = f"LOT{(i+j):04d}"
            
            # Ajouter DLC si le comptage le requiert
            if counting.dlc and product.dlc:
                detail_data['dlc'] = (now + timedelta(days=30 * (j + 1))).date()
            
            counting_detail = CountingDetail(**detail_data)
            counting_detail.reference = generate_unique_reference('CD', cd_index)
            counting_detail.save()
            counting_details.append(counting_detail)
            cd_index += 1
            
            info = f"{product.Short_Description[:30]}"
            if detail_data.get('n_lot'):
                info += f" [LOT: {detail_data['n_lot']}]"
            if detail_data.get('dlc'):
                info += f" [DLC: {detail_data['dlc']}]"
            
            print(f"   ✓ CountingDetail créé: {info} - Qté: {quantity} ({counting_detail.reference})")
    
    return counting_details


def create_nserie_inventory(counting_details, countings):
    """Créer des numéros de série pour les comptages qui en nécessitent"""
    print("\n🔢 Création des numéros de série d'inventaire (NSerieInventory)...")
    
    nserie_inventories = []
    
    # Filtrer les comptages qui nécessitent des numéros de série
    countings_with_nserie = [c for c in countings if c.n_serie]
    
    if not countings_with_nserie:
        print("   ℹ️  Aucun comptage ne nécessite de numéros de série")
        return []
    
    # Filtrer les CountingDetail correspondants
    ns_index = 0
    for counting in countings_with_nserie[:5]:
        details = [cd for cd in counting_details if cd.counting == counting and cd.product and cd.product.n_serie]
        
        for detail in details[:3]:  # Limiter à 3 détails par comptage
            # Créer plusieurs numéros de série par détail
            for i in range(min(3, detail.quantity_inventoried)):
                n_serie_value = f"SN{detail.product.Internal_Product_Code}-{detail.id:04d}-{i+1:03d}"
                
                nserie_inv = NSerieInventory(
                    n_serie=n_serie_value,
                    counting_detail=detail
                )
                nserie_inv.reference = generate_unique_reference('NS', ns_index)
                nserie_inv.save()
                nserie_inventories.append(nserie_inv)
                ns_index += 1
                print(f"   ✓ NSerieInventory créé: {detail.product.Short_Description[:30]} - {n_serie_value} ({nserie_inv.reference})")
    
    return nserie_inventories


def create_ecart_comptage(counting_details, inventories):
    """Créer des écarts de comptage"""
    print("\n⚠️  Création des écarts de comptage (EcartComptage)...")
    
    ecarts = []
    
    # Grouper les détails de comptage par produit et emplacement
    details_by_product_location = {}
    for detail in counting_details:
        key = (detail.product_id, detail.location_id)
        if key not in details_by_product_location:
            details_by_product_location[key] = []
        details_by_product_location[key].append(detail)
    
    # Créer des écarts pour les produits comptés plusieurs fois
    ecart_index = 0
    for (product_id, location_id), details in details_by_product_location.items():
        if len(details) >= 2:  # Au moins 2 comptages pour créer un écart
            detail1 = details[0]
            detail2 = details[1]
            detail3 = details[2] if len(details) >= 3 else None
            
            # Calculer l'écart
            ecart_value = abs(detail1.quantity_inventoried - detail2.quantity_inventoried)
            
            # Ne créer un écart que s'il y a une différence
            if ecart_value > 0:
                ecart_data = {
                    'inventory': detail1.counting.inventory,
                    'ligne_comptage_1': detail1,
                    'ligne_comptage_2': detail2,
                    'ligne_comptage_3': detail3,
                    'ecart': ecart_value,
                    'result': None,  # Sera résolu plus tard
                    'justification': '',
                    'resolved': False
                }
                
                ecart = EcartComptage(**ecart_data)
                ecart.reference = generate_unique_reference('ECT', ecart_index)
                ecart.save()
                ecarts.append(ecart)
                ecart_index += 1
                print(f"   ✓ Écart créé: {detail1.product.Short_Description[:30]} - Écart: {ecart_value} unités ({ecart.reference})")
    
    # Créer aussi quelques écarts résolus
    if len(ecarts) > 0:
        print("\n   📝 Résolution de quelques écarts...")
        for i, ecart in enumerate(ecarts[:3]):  # Résoudre les 3 premiers
            ecart.result = (ecart.ligne_comptage_1.quantity_inventoried + ecart.ligne_comptage_2.quantity_inventoried) // 2
            ecart.justification = f"Écart résolu par comptage de contrôle. Valeur retenue: {ecart.result}"
            ecart.resolved = True
            ecart.save()
            print(f"   ✓ Écart résolu: {ecart.reference} - Résultat: {ecart.result}")
    
    return ecarts


def print_summary(data):
    """Afficher un résumé des données créées"""
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES DONNÉES CRÉÉES")
    print("="*80)
    
    print(f"\n👥 Utilisateurs: {len(data['users'])}")
    for user in data['users']:
        compte_name = user.compte.account_name if user.compte else 'Aucun compte'
        print(f"   └─ {user.username} ({user.prenom} {user.nom}) - {compte_name}")
    print(f"\n👤 Personnes: {len(data['personnes'])}")
    print(f"📦 Inventaires: {len(data['inventories'])}")
    print(f"   └─ EN PREPARATION: {len([i for i in data['inventories'] if i.status == 'EN PREPARATION'])}")
    print(f"   └─ EN REALISATION: {len([i for i in data['inventories'] if i.status == 'EN REALISATION'])}")
    print(f"   └─ TERMINE: {len([i for i in data['inventories'] if i.status == 'TERMINE'])}")
    print(f"   └─ CLOTURE: {len([i for i in data['inventories'] if i.status == 'CLOTURE'])}")
    
    print(f"\n⚙️  Settings: {len(data['settings'])}")
    print(f"📅 Plannings: {len(data['plannings'])}")
    print(f"🔢 Comptages: {len(data['countings'])}")
    print(f"   └─ Avec n_serie: {len([c for c in data['countings'] if c.n_serie])}")
    print(f"   └─ Avec n_lot: {len([c for c in data['countings'] if c.n_lot])}")
    print(f"   └─ Avec DLC: {len([c for c in data['countings'] if c.dlc])}")
    print(f"   └─ Avec variantes: {len([c for c in data['countings'] if c.is_variant])}")
    
    print(f"\n💼 Jobs: {len(data['jobs'])}")
    for status in ['EN ATTENTE', 'AFFECTE', 'PRET', 'TRANSFERT', 'ENTAME', 'VALIDE', 'TERMINE', 'SAISIE MANUELLE']:
        count = len([j for j in data['jobs'] if j.status == status])
        if count > 0:
            print(f"   └─ {status}: {count}")
    
    print(f"\n📋 JobDetails: {len(data['job_details'])}")
    print(f"👥 Affectations: {len(data['assignments'])}")
    print(f"🔧 Ressources: {len(data['ressources'])}")
    print(f"🔗 JobDetailRessources: {len(data['job_detail_ressources'])}")
    print(f"🔗 InventoryDetailRessources: {len(data['inventory_detail_ressources'])}")
    print(f"📊 CountingDetails: {len(data['counting_details'])}")
    print(f"🔢 NSerieInventory: {len(data['nserie_inventories'])}")
    print(f"⚠️  Écarts de comptage: {len(data['ecarts'])}")
    print(f"   └─ Résolus: {len([e for e in data['ecarts'] if e.resolved])}")
    print(f"   └─ Non résolus: {len([e for e in data['ecarts'] if not e.resolved])}")
    
    print("\n" + "="*80)
    print("✅ DONNÉES CRÉÉES AVEC SUCCÈS!")
    print("="*80)


def main():
    """Fonction principale pour créer toutes les données"""
    print("\n" + "="*80)
    print("🚀 DÉMARRAGE DU SCRIPT DE POPULATION DES DONNÉES INVENTORY")
    print("="*80)
    
    try:
        # 1. Nettoyer les anciennes données
        clear_inventory_data()
        
        # 2. Créer les données de base
        users = create_test_users()
        personnes = create_personnes()
        inventories = create_inventories()
        settings = create_settings(inventories)
        plannings = create_plannings(inventories)
        countings = create_countings(inventories)
        jobs = create_jobs(inventories)
        
        # 3. Créer les détails et affectations
        job_details = create_job_details(jobs, countings)
        assignments = create_assignments(jobs, personnes, countings, users)
        
        # 4. Créer les ressources
        ressources = create_ressources_if_needed()
        job_detail_ressources = create_job_detail_ressources(jobs, ressources)
        inventory_detail_ressources = create_inventory_detail_ressources(inventories, ressources)
        
        # 5. Créer les détails de comptage
        counting_details = create_counting_details(countings)
        nserie_inventories = create_nserie_inventory(counting_details, countings)
        
        # 6. Créer les écarts
        ecarts = create_ecart_comptage(counting_details, inventories)
        
        # 7. Afficher le résumé
        data = {
            'users': users,
            'personnes': personnes,
            'inventories': inventories,
            'settings': settings,
            'plannings': plannings,
            'countings': countings,
            'jobs': jobs,
            'job_details': job_details,
            'assignments': assignments,
            'ressources': ressources,
            'job_detail_ressources': job_detail_ressources,
            'inventory_detail_ressources': inventory_detail_ressources,
            'counting_details': counting_details,
            'nserie_inventories': nserie_inventories,
            'ecarts': ecarts,
        }
        
        print_summary(data)
        
        print("\n💡 Vous pouvez maintenant:")
        print("   • Accéder à l'admin Django pour voir les données")
        print("   • Tester les APIs avec ces données")
        print("   • Utiliser ces données pour vos tests unitaires")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())

