#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API de statistiques des warehouses d'un inventaire.

Ce script démontre comment utiliser l'API pour récupérer les statistiques
des warehouses associés à un inventaire spécifique.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

class WarehouseStatsAPI:
    """Classe pour interagir avec l'API de statistiques des warehouses"""
    
    def __init__(self, base_url: str, token: str):
        """
        Initialise le client API
        
        Args:
            base_url: URL de base de l'API (ex: http://localhost:8000)
            token: Token d'authentification
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
    
    def get_warehouse_stats(self, inventory_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques des warehouses pour un inventaire
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Dict[str, Any]: Données de réponse de l'API ou None en cas d'erreur
        """
        url = f"{self.base_url}/api/inventory/{inventory_id}/warehouse-stats/"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erreur {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Erreur de connexion: {e}")
            return None
    
    def print_stats(self, data: Dict[str, Any]) -> None:
        """
        Affiche les statistiques de manière formatée
        
        Args:
            data: Données de réponse de l'API
        """
        if data['status'] != 'success':
            print(f"Erreur: {data['message']}")
            return
        
        print(f"\n📊 Statistiques des Warehouses - Inventaire {data['inventory_id']}")
        print("=" * 60)
        print(f"Nombre total de warehouses: {data['warehouses_count']}")
        print()
        
        if not data['data']:
            print("Aucun warehouse associé à cet inventaire.")
            return
        
        # Afficher les statistiques par warehouse
        for i, warehouse in enumerate(data['data'], 1):
            print(f"🏢 Warehouse {i}: {warehouse['warehouse_name']}")
            print(f"   Référence: {warehouse['warehouse_reference']}")
            print(f"   📋 Jobs: {warehouse['jobs_count']}")
            print(f"   👥 Équipes: {warehouse['teams_count']}")
            print()
        
        # Calculer les totaux
        total_jobs = sum(w['jobs_count'] for w in data['data'])
        total_teams = sum(w['teams_count'] for w in data['data'])
        
        print("📈 Totaux:")
        print(f"   📋 Jobs totaux: {total_jobs}")
        print(f"   👥 Équipes totales: {total_teams}")
    
    def export_to_json(self, data: Dict[str, Any], filename: str) -> None:
        """
        Exporte les données au format JSON
        
        Args:
            data: Données de réponse de l'API
            filename: Nom du fichier de sortie
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Données exportées vers {filename}")
        except Exception as e:
            print(f"❌ Erreur lors de l'export: {e}")
    
    def export_to_csv(self, data: Dict[str, Any], filename: str) -> None:
        """
        Exporte les données au format CSV
        
        Args:
            data: Données de réponse de l'API
            filename: Nom du fichier de sortie
        """
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # En-têtes
                writer.writerow([
                    'Warehouse ID',
                    'Référence',
                    'Nom',
                    'Jobs',
                    'Équipes'
                ])
                
                # Données
                for warehouse in data['data']:
                    writer.writerow([
                        warehouse['warehouse_id'],
                        warehouse['warehouse_reference'],
                        warehouse['warehouse_name'],
                        warehouse['jobs_count'],
                        warehouse['teams_count']
                    ])
            
            print(f"✅ Données exportées vers {filename}")
        except ImportError:
            print("❌ Module csv non disponible")
        except Exception as e:
            print(f"❌ Erreur lors de l'export CSV: {e}")


def main():
    """Fonction principale"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"  # Modifier selon votre configuration
    TOKEN = "your_token_here"  # Remplacer par votre token d'authentification
    
    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("Usage: python warehouse_stats_example.py <inventory_id> [export_format]")
        print("  export_format: 'json' ou 'csv' (optionnel)")
        print("\nExemples:")
        print("  python warehouse_stats_example.py 1")
        print("  python warehouse_stats_example.py 1 json")
        print("  python warehouse_stats_example.py 1 csv")
        sys.exit(1)
    
    try:
        inventory_id = int(sys.argv[1])
    except ValueError:
        print("❌ L'ID de l'inventaire doit être un nombre entier")
        sys.exit(1)
    
    export_format = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Créer le client API
    api = WarehouseStatsAPI(BASE_URL, TOKEN)
    
    print(f"🔍 Récupération des statistiques pour l'inventaire {inventory_id}...")
    
    # Récupérer les données
    data = api.get_warehouse_stats(inventory_id)
    
    if data is None:
        print("❌ Impossible de récupérer les données")
        sys.exit(1)
    
    # Afficher les statistiques
    api.print_stats(data)
    
    # Export si demandé
    if export_format:
        if export_format.lower() == 'json':
            filename = f"warehouse_stats_inventory_{inventory_id}.json"
            api.export_to_json(data, filename)
        elif export_format.lower() == 'csv':
            filename = f"warehouse_stats_inventory_{inventory_id}.csv"
            api.export_to_csv(data, filename)
        else:
            print(f"❌ Format d'export non reconnu: {export_format}")
            print("Formats supportés: 'json', 'csv'")


if __name__ == "__main__":
    main() 