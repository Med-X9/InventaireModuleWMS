#!/usr/bin/env python3
"""
Exemple pratique d'utilisation des APIs d'avancement des emplacements par job et par counting
"""

import requests
import json
from datetime import datetime
import time

class JobProgressMonitor:
    """
    Classe pour surveiller l'avancement des jobs et inventaires
    """
    
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_job_progress(self, job_id):
        """
        Récupère l'avancement d'un job spécifique
        """
        url = f"{self.base_url}/jobs/{job_id}/progress-by-counting/"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erreur {response.status_code}: {response.text}")
            return None
    
    def get_inventory_progress(self, inventory_id):
        """
        Récupère l'avancement global d'un inventaire
        """
        url = f"{self.base_url}/inventory/{inventory_id}/progress-by-counting/"
        response = self.session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erreur {response.status_code}: {response.text}")
            return None
    
    def display_job_progress(self, job_id):
        """
        Affiche l'avancement d'un job de manière formatée
        """
        data = self.get_job_progress(job_id)
        
        if not data or not data.get('success'):
            print(f"❌ Impossible de récupérer l'avancement du job {job_id}")
            return
        
        job_data = data['data']
        print(f"\n📊 AVANCEMENT DU JOB {job_data['job_reference']}")
        print("=" * 60)
        print(f"📋 Inventaire: {job_data['inventory_reference']}")
        print(f"🏢 Entrepôt: {job_data['warehouse_name']}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        for progress in job_data['progress_by_counting']:
            print(f"🔄 Counting {progress['counting_order']} - {progress['counting_count_mode']}")
            print(f"   📈 Progression: {progress['completed_emplacements']}/{progress['total_emplacements']} ({progress['progress_percentage']}%)")
            
            # Barre de progression visuelle
            bar_length = 30
            filled_length = int(bar_length * progress['progress_percentage'] / 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            print(f"   [{bar}] {progress['progress_percentage']}%")
            
            # Détails des emplacements
            if progress['emplacements_details']:
                print(f"   📍 Emplacements:")
                completed = sum(1 for emp in progress['emplacements_details'] if emp['status'] == 'TERMINE')
                pending = len(progress['emplacements_details']) - completed
                print(f"      ✅ Terminés: {completed}")
                print(f"      ⏳ En attente: {pending}")
                
                # Afficher quelques exemples d'emplacements
                for i, emp in enumerate(progress['emplacements_details'][:3]):
                    status_icon = "✅" if emp['status'] == 'TERMINE' else "⏳"
                    print(f"      {status_icon} {emp['location_reference']} ({emp['sous_zone_name']})")
                
                if len(progress['emplacements_details']) > 3:
                    print(f"      ... et {len(progress['emplacements_details']) - 3} autres")
            print()
    
    def display_inventory_progress(self, inventory_id):
        """
        Affiche l'avancement global d'un inventaire de manière formatée
        """
        data = self.get_inventory_progress(inventory_id)
        
        if not data or not data.get('success'):
            print(f"❌ Impossible de récupérer l'avancement de l'inventaire {inventory_id}")
            return
        
        inventory_data = data['data']
        print(f"\n🏭 AVANCEMENT GLOBAL DE L'INVENTAIRE {inventory_data['inventory_reference']}")
        print("=" * 70)
        print(f"📊 Total des jobs: {inventory_data['total_jobs']}")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        for progress in inventory_data['progress_by_counting']:
            print(f"🔄 Counting {progress['counting_order']} - {progress['counting_count_mode']}")
            print(f"   📈 Progression globale: {progress['completed_emplacements']}/{progress['total_emplacements']} ({progress['progress_percentage']}%)")
            
            # Barre de progression visuelle
            bar_length = 40
            filled_length = int(bar_length * progress['progress_percentage'] / 100)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)
            print(f"   [{bar}] {progress['progress_percentage']}%")
            
            # Progression par job
            if progress['jobs_progress']:
                print(f"   📋 Détail par job:")
                for job_progress in progress['jobs_progress']:
                    job_bar_length = 20
                    job_filled_length = int(job_bar_length * job_progress['progress_percentage'] / 100)
                    job_bar = "█" * job_filled_length + "░" * (job_bar_length - job_filled_length)
                    print(f"      {job_progress['job_reference']}: [{job_bar}] {job_progress['progress_percentage']}%")
            print()
    
    def monitor_job_realtime(self, job_id, interval=30):
        """
        Surveille un job en temps réel avec mise à jour automatique
        """
        print(f"🔍 Surveillance en temps réel du job {job_id}")
        print(f"⏱️  Mise à jour toutes les {interval} secondes")
        print("Appuyez sur Ctrl+C pour arrêter")
        print()
        
        try:
            while True:
                self.display_job_progress(job_id)
                print(f"⏰ Prochaine mise à jour dans {interval} secondes...")
                time.sleep(interval)
                print("\n" + "="*60 + "\n")
                
        except KeyboardInterrupt:
            print("\n🛑 Surveillance arrêtée par l'utilisateur")
    
    def compare_jobs_progress(self, job_ids):
        """
        Compare l'avancement de plusieurs jobs
        """
        print(f"📊 COMPARAISON DE L'AVANCEMENT DES JOBS")
        print("=" * 60)
        
        jobs_data = []
        for job_id in job_ids:
            data = self.get_job_progress(job_id)
            if data and data.get('success'):
                jobs_data.append(data['data'])
        
        if not jobs_data:
            print("❌ Aucune donnée de job disponible")
            return
        
        # Afficher un tableau comparatif
        print(f"{'Job':<15} {'Inventaire':<15} {'Counting 1':<12} {'Counting 2':<12}")
        print("-" * 60)
        
        for job_data in jobs_data:
            job_ref = job_data['job_reference']
            inventory_ref = job_data['inventory_reference']
            
            counting_progress = {}
            for progress in job_data['progress_by_counting']:
                counting_progress[progress['counting_order']] = progress['progress_percentage']
            
            counting_1 = f"{counting_progress.get(1, 0):.1f}%" if 1 in counting_progress else "N/A"
            counting_2 = f"{counting_progress.get(2, 0):.1f}%" if 2 in counting_progress else "N/A"
            
            print(f"{job_ref:<15} {inventory_ref:<15} {counting_1:<12} {counting_2:<12}")

def main():
    """
    Fonction principale avec exemples d'utilisation
    """
    monitor = JobProgressMonitor()
    
    print("🚀 Exemple d'utilisation des APIs d'avancement")
    print("=" * 50)
    
    # Exemple 1: Afficher l'avancement d'un job
    print("\n1️⃣  Affichage de l'avancement d'un job")
    job_id = 1  # Remplacez par un ID de job existant
    monitor.display_job_progress(job_id)
    
    # Exemple 2: Afficher l'avancement global d'un inventaire
    print("\n2️⃣  Affichage de l'avancement global d'un inventaire")
    inventory_id = 1  # Remplacez par un ID d'inventaire existant
    monitor.display_inventory_progress(inventory_id)
    
    # Exemple 3: Comparer plusieurs jobs
    print("\n3️⃣  Comparaison de l'avancement de plusieurs jobs")
    job_ids = [1, 2, 3]  # Remplacez par des IDs de jobs existants
    monitor.compare_jobs_progress(job_ids)
    
    # Exemple 4: Surveillance en temps réel (décommenter pour utiliser)
    # print("\n4️⃣  Surveillance en temps réel")
    # monitor.monitor_job_realtime(job_id, interval=10)
    
    print("\n✅ Exemples terminés!")

if __name__ == "__main__":
    main() 